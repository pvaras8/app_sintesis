import streamlit as st
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuración de autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("healthy-bazaar-443012-v8-094bce9348c8.json", scope)
client = gspread.authorize(creds)

# Abrir la hoja de cálculo usando el ID (reemplaza por el ID real de tu hoja)
sheet_id = "1Y_kS6fxQC09C_vlOmKovSr9DmlgxODYm4fl_zCZmi5I"  # Cambia esto por el ID real de tu hoja
sheet = client.open_by_key(sheet_id).sheet1

# Función para cargar datos desde Google Sheets
def load_data():
    records = sheet.get_all_records()  # Lee todos los datos como una lista de diccionarios
    return pd.DataFrame(records)  # Convierte a DataFrame

# Función para actualizar datos en la hoja de cálculo
def save_data(classifications):
    records = sheet.get_all_records()  # Lista de todas las filas
    for smiles, classification in classifications.items():
        for i, record in enumerate(records):
            if record["SMILES"] == smiles:
                sheet.update_cell(i + 2, 4, classification)  # Columna 4 corresponde a "Clasificación"

# Cargar los datos desde la hoja de cálculo
data = load_data()

# Interfaz de usuario en Streamlit
st.title("Clasificación de Moléculas")

if "Clasificación" not in data.columns:
    st.error("La columna 'Clasificación' no existe en la hoja de cálculo. Verifica tu archivo.")
else:
    # Detectar filas donde la clasificación está vacía
    data["Clasificación"] = data["Clasificación"].replace("", None)  # Reemplaza celdas vacías por None (nulo)
    sin_clasificar = data[data["Clasificación"].isna()]  # Filtra filas donde la clasificación es nula

    if sin_clasificar.empty:
        st.write("¡Todas las moléculas han sido clasificadas! 🎉")
    else:
        # Mostrar hasta 10 moléculas sin clasificar
        moleculas_a_mostrar = sin_clasificar.head(10)

        st.write("Clasifica las siguientes moléculas:")
        classifications = {}  # Diccionario para almacenar clasificaciones

        for index, row in moleculas_a_mostrar.iterrows():
            smiles = row["SMILES"]
            mol = Chem.MolFromSmiles(smiles)
            st.image(Draw.MolToImage(mol), caption=f"Molécula: {smiles}", use_column_width=True)

            # Capturar clasificación para cada molécula
            decision = st.radio(
                f"Clasificación para {smiles}:", ["Buena", "Mala"], key=smiles
            )
            classifications[smiles] = decision

        # Botón para guardar clasificaciones
        if st.button("Guardar clasificaciones"):
            save_data(classifications)
            st.success("Clasificaciones guardadas correctamente.")
            st.experimental_rerun()

# Botón para descargar el archivo actualizado
st.markdown("### Descargar clasificaciones actuales")
csv_data = data.to_csv(index=False)
st.download_button(
    label="Descargar CSV",
    data=csv_data,
    file_name="clasificaciones_actualizadas.csv",
    mime="text/csv",
)
