import streamlit as st
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Draw
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuración de autenticación con Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

if "gcp_service_account" not in st.secrets:
    st.error("Falta la configuración de Google Cloud en Streamlit Secrets.")
    st.stop()

credentials_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

# Abrir la hoja de cálculo usando el ID (reemplaza por el ID real de tu hoja)
sheet_id = "1AVEHLBoKES1zxb0W3wa2MS9j3JdP1_KbhGuLeUJ7V4o"  # Cambia esto por el ID real de tu hoja
sheet = client.open_by_key(sheet_id).sheet1


def ensure_comment_column():
    headers = sheet.row_values(1)
    if "Comentarios" not in headers:
        sheet.update_cell(1, len(headers) + 1, "Comentarios")


# Función para cargar datos desde Google Sheets
def load_data():
    records = sheet.get_all_records()  # Lee todos los datos como una lista de diccionarios
    df = pd.DataFrame(records)  # Convierte a DataFrame
    if "Comentarios" not in df.columns:
        df["Comentarios"] = ""
    return df


# Función para actualizar datos en la hoja de cálculo
def save_data(classifications):
    ensure_comment_column()
    records = sheet.get_all_records()  # Lista de todas las filas
    headers = sheet.row_values(1)

    classification_col = headers.index("Clasificacion") + 1
    comment_col = headers.index("Comentarios") + 1

    for smiles, payload in classifications.items():
        classification = payload["Clasificacion"]
        comment = payload.get("Comentarios", "")
        for i, record in enumerate(records):
            if record["SMILES"] == smiles:
                sheet.update_cell(i + 2, classification_col, classification)
                sheet.update_cell(i + 2, comment_col, comment)
                break

# Cargar los datos desde la hoja de cálculo
data = load_data()

# Interfaz de usuario en Streamlit
st.title("Clasificación de Moléculas")

if "Clasificacion" not in data.columns:
    st.error("La columna 'Clasificacion' no existe en la hoja de cálculo. Verifica tu archivo.")
else:
    data["Clasificacion"] = data["Clasificacion"].replace("", None)
    data["Comentarios"] = data["Comentarios"].fillna("")
    sin_clasificar = data[data["Clasificacion"].isna()]

    if sin_clasificar.empty:
        st.write("¡Todas las moléculas han sido clasificadas! 🎉")
    else:
        moleculas_a_mostrar = sin_clasificar.head(10)

        st.write("Clasifica las siguientes moléculas:")
        classifications = {}

        for index, row in moleculas_a_mostrar.iterrows():
            smiles = row["SMILES"]
            mol = Chem.MolFromSmiles(smiles)
            st.image(Draw.MolToImage(mol), caption=f"Molécula: {smiles}", use_column_width=True)

            decision = st.radio(
                f"Clasificacion para {smiles}:", ["Buena", "Mala"], key=f"clasif_{smiles}"
            )
            comment = st.text_area(
                f"Comentarios opcional para {smiles}:",
                value="",
                key=f"comentario_{smiles}",
                placeholder="Ej: estructura prometedora, alerta de toxicidad, etc. (opcional)",
            )
            classifications[smiles] = {"Clasificacion": decision, "Comentarios": comment}

        if st.button("Guardar clasificaciones"):
            save_data(classifications)
            st.success("Clasificaciones y comentarios guardados correctamente.")
            st.rerun()

# Botón para descargar el archivo actualizado
st.markdown("### Descargar clasificaciones actuales")
csv_data = data.to_csv(index=False)
st.download_button(
    label="Descargar CSV",
    data=csv_data,
    file_name="clasificaciones_actualizadas.csv",
    mime="text/csv",
)
