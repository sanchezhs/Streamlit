# import pandas as pd
# import re

# def parse_weight_series(row):
#     pesos_raw = str(row["Peso (kg)"]).strip()
#     repeticiones_raw = str(row["Repeticiones"]).strip()

#     # Detectar múltiples series si hay varias comas y más de un número
#     if "," in pesos_raw:
#         # Extraer números con o sin decimales
#         pesos = re.findall(r"\d+(?:\.\d+)?", pesos_raw)
#         pesos = list(map(float, pesos)) if pesos else []
#     else:
#         try:
#             pesos = [float(pesos_raw)] if pesos_raw else []
#         except Exception:
#             pesos = []

#     # Repeticiones por serie
#     reps = [int(r) for r in repeticiones_raw.split(',') if r.strip().isdigit()]
#     return pd.Series({
#         "Peso medio": round(sum(pesos) / len(pesos), 2) if pesos else None,
#         "Reps totales": round(sum(reps), 2) if reps else None,
#         "Series": row['Series']
#     })

# def parse_xlsx(excel_path, output_csv):
#     # Cargar todas las hojas
#     xls = pd.ExcelFile(excel_path)
#     sheets_data = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

#     # Unir todas las hojas
#     all_data = []
#     for sheet_name, df in sheets_data.items():
#         df = df.rename(columns={
#             df.columns[0]: "Ejercicio",
#             df.columns[1]: "Peso (kg)",
#             df.columns[2]: "Series",
#             df.columns[3]: "Repeticiones"
#         })
#         df = df.dropna(subset=["Ejercicio"])
#         df["Semana"] = sheet_name
#         df[["Peso medio", "Reps totales", "Series"]] = df.apply(parse_weight_series, axis=1)
#         all_data.append(df[["Ejercicio", "Semana", "Peso medio", "Reps totales", "Series"]])

#     # Concatenar y guardar como CSV
#     final_df = pd.concat(all_data, ignore_index=True)
#     final_df = final_df[~final_df.Ejercicio.str.contains("Ejercicio")]
#     final_df.to_csv(output_csv, index=False)

#     print(f"Archivo guardado como: {output_csv}")

# if __name__ == "__main__":
#     # Ruta al archivo Excel original
#     excel_path = "Progreso.xlsx"
#     output_csv = "progreso_entrenamiento.csv"

#     parse_xlsx(excel_path, output_csv)

import pandas as pd

def expandir_series(row):
    pesos_raw = str(row["Peso (kg)"]).strip()
    reps_raw = str(row["Repeticiones"]).strip()
    # breakpoint()
    try:
        pesos = [float(p.strip()) for p in pesos_raw.split(",") if p.strip()]
    except ValueError:
        breakpoint()
    reps = [int(r.strip()) for r in reps_raw.split(",") if r.strip().isdigit()]

    if len(pesos) == 1 and len(reps) > 1:
        pesos = pesos * len(reps)
    elif len(pesos) < len(reps):
        diferencia = len(reps) - len(pesos)
        if len(pesos) > 0:
            pesos += [pesos[-1]] * diferencia

    series_expandidas = []
    for i in range(min(len(pesos), len(reps))):
        series_expandidas.append({
            "Ejercicio": row["Ejercicio"],
            "Semana": row["Semana"],
            "Serie": i + 1,
            "Peso": pesos[i],
            "Reps": reps[i]
        })
    return series_expandidas

def parse_xlsx(excel_path, output_csv):
    xls = pd.ExcelFile(excel_path)
    sheets_data = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

    all_series = []
    for sheet_name, df in sheets_data.items():
        df = df.rename(columns={
            df.columns[0]: "Ejercicio",
            df.columns[1]: "Peso (kg)",
            df.columns[2]: "Series",
            df.columns[3]: "Repeticiones"
        })
        df = df.dropna(subset=["Ejercicio"])
        df["Semana"] = sheet_name

        for i, row in df.iterrows():
            if row['Ejercicio'] == "Ejercicio":
                continue
            all_series.extend(expandir_series(row))

    final_df = pd.DataFrame(all_series)

    # Calcular peso medio y repeticiones totales por ejercicio y semana
    resumen = final_df.groupby(["Ejercicio", "Semana"]).agg({
        "Peso": "mean",
        "Reps": "sum"
    }).reset_index().rename(columns={
        "Peso": "Peso medio",
        "Reps": "Reps totales"
    })

    # Unir al DataFrame de series
    final_df = final_df.merge(resumen, on=["Ejercicio", "Semana"], how="left")
    final_df.to_csv(output_csv, index=False)
    # Redondear los valores
    final_df["Peso medio"] = final_df["Peso medio"].round(2)
    print(f"Archivo guardado como: {output_csv}")

if __name__ == "__main__":
    excel_path = "data/Progreso.xlsx"
    output_csv = "data/progreso_entrenamiento.csv"
    parse_xlsx(excel_path, output_csv)
