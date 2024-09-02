import os
import chardet
import pandas as pd
from flask import Flask, render_template, request, send_file, flash, session

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def detect_anomalies(df):
    anomalies = {}
    for column in df.columns:
        for index, value in df[column].items():
            error_messages = []
            if isinstance(value, str):
                if value.strip() != value:
                    error_messages.append('Espacios en blanco innecesarios')
                if '\n' in value or '\r' in value:
                    error_messages.append('Salto de línea encontrado')
            if error_messages:
                key = (index + 2, column)
                if key not in anomalies:
                    anomalies[key] = []
                anomalies[key].extend(error_messages)
    anomaly_list = [(index, column, ', '.join(errors), df.at[index-2, column]) for (index, column), errors in anomalies.items()]
    return anomaly_list

def correct_anomalies(df):
    corrected_df = df.copy()
    for column in corrected_df.columns:
        corrected_df[column] = corrected_df[column].apply(lambda x: x.strip() if isinstance(x, str) else x)
        corrected_df[column] = corrected_df[column].apply(lambda x: x.replace('\n', '').replace('\r', '') if isinstance(x, str) else x)
    return corrected_df

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No se seleccionó ningún archivo.', 'error')
            return render_template('index.html')
        
        file_path = os.path.join(os.getcwd(), file.filename)
        file.save(file_path)

        # Detectar la codificación del archivo
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        
        encoding = result['encoding']

        # Convertir a ANSI si la codificación es incorrecta
        if encoding not in ['ISO-8859-1', 'ascii']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                corrected_file_path = os.path.join(os.getcwd(), 'corrected_' + file.filename)
                df.to_csv(corrected_file_path, index=False, encoding='ISO-8859-1')
                flash(f'El archivo ha sido convertido automáticamente a formato ANSI (Archivo Delimitado por Comas).', 'success')
                file_path = corrected_file_path  # Actualizar el path al archivo corregido
            except Exception as e:
                flash(f'Error al convertir el archivo: {e}', 'error')
                return render_template('index.html')

        try:
            # Leer el archivo CSV corregido
            df = pd.read_csv(file_path, encoding='ISO-8859-1')

            # Validar si contiene la cabecera 'TELEFONO'
            if 'TELEFONO' not in df.columns:
                flash('El archivo CSV no contiene la cabecera requerida: TELEFONO.', 'error')
                return render_template('index.html')

            anomalies = detect_anomalies(df)
            if not anomalies:
                flash('No se detectaron anomalías en el archivo.', 'success')
            else:
                flash('Se encontraron anomalías.', 'error')

            corrected_df = correct_anomalies(df)
            corrected_file_path = os.path.join(os.getcwd(), 'corrected_' + file.filename)
            corrected_df.to_csv(corrected_file_path, index=False, encoding='ISO-8859-1')

            # Guardar la ruta del archivo corregido en la sesión
            session['corrected_file_path'] = corrected_file_path

            return render_template('index.html', anomalies=anomalies)

        except Exception as e:
            flash(f'Error al procesar el archivo: {e}', 'error')

    return render_template('index.html')

@app.route('/download')
def download_file():
    path = session.get('corrected_file_path')
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        flash('El archivo corregido no se encuentra disponible para descargar.', 'error')
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
