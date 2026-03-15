from fastapi import APIRouter, Query, HTTPException
import logging
from datetime import datetime
from app.core import extract, config, processing
from typing import Literal

router = APIRouter(tags=["Finance"])
logger = logging.getLogger("finance")
logger.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formato de logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)

@router.get("/years")
def get_available_years():
    current_year = datetime.now().year
    return {
        "years": [current_year, current_year - 1, current_year - 2, current_year - 3]
    }


@router.get("/summary/{year}")
def get_summary(
    year: int,
    currency: Literal["COP", "USD"] = "COP",
    usd_to_cop: float = Query(5000.0, gt=0)
):
    """
    Devuelve el resumen financiero del año.

    - year: año de los datos
    - currency: moneda de salida (COP o USD)
    - usd_to_cop: tasa USD → COP usada para conversión
    """

    # Validaciones tempranas
    if usd_to_cop <= 0:
        raise HTTPException(status_code=400, detail="La tasa de conversión debe ser mayor a 0")

    if currency.upper() not in ["COP", "USD"]:
        raise HTTPException(status_code=400, detail="Moneda inválida. Debe ser 'COP' o 'USD'.")

    try:
        # Cargar DataFrame
        df = extract.extract_dataset(config.DATASET_ROOT_PATH, year)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para el año {year}")

        # Generar resumen
        resumen = processing.summarize_dataframe(
            df, usd_to_cop=usd_to_cop, currency=currency.upper()
        )

        return resumen

    except FileNotFoundError:
        logger.exception(f"Dataset del año {year} no encontrado")
        raise HTTPException(status_code=404, detail=f"Dataset del año {year} no encontrado")

    except ValueError as ve:
        logger.exception(f"Error de procesamiento para el año {year}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.exception(f"Error interno procesando resumen para {year}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/byEntity/{year}")
def get_dataByEntity(
    year: int,
    currency: Literal["COP", "USD"] = "USD",
    usd_to_cop: float = Query(5000.0, gt=0)
):
    # Validaciones tempranas
    if usd_to_cop <= 0:
        raise HTTPException(status_code=400, detail="La tasa de conversión debe ser mayor a 0")

    if currency.upper() not in ["COP", "USD"]:
        raise HTTPException(status_code=400, detail="Moneda inválida. Debe ser 'COP' o 'USD'.")

    try:
        # Cargar DataFrame
        df = extract.extract_dataset(config.DATASET_ROOT_PATH, year)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para el año {year}")

        # Generar resumen
        resumen = extract.getBalanceByEntity(
            df, usd_to_cop=usd_to_cop, currency=currency.upper()
        )

        return resumen

    except FileNotFoundError:
        logger.exception(f"Dataset del año {year} no encontrado")
        raise HTTPException(status_code=404, detail=f"Dataset del año {year} no encontrado")

    except ValueError as ve:
        logger.exception(f"Error de procesamiento para el año {year}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.exception(f"Error interno procesando resumen para {year}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/byMonth/{year}")
def get_dataByMonth(
    year: int,
    currency: Literal["COP", "USD"] = "USD",
    usd_to_cop: float = Query(5000.0, gt=0)
):
    # Validaciones tempranas
    if usd_to_cop <= 0:
        raise HTTPException(status_code=400, detail="La tasa de conversión debe ser mayor a 0")

    if currency.upper() not in ["COP", "USD"]:
        raise HTTPException(status_code=400, detail="Moneda inválida. Debe ser 'COP' o 'USD'.")

    try:
        # Cargar DataFrame
        df = extract.extract_dataset(config.DATASET_ROOT_PATH, year)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para el año {year}")

        # Generar resumen
        resumen = extract.getBalanceByMonth(
            df, usd_to_cop=usd_to_cop, currency=currency.upper()
        )
        #print( resumen)
        return resumen

    except FileNotFoundError:
        logger.exception(f"Dataset del año {year} no encontrado")
        raise HTTPException(status_code=404, detail=f"Dataset del año {year} no encontrado")

    except ValueError as ve:
        logger.exception(f"Error de procesamiento para el año {year}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.exception(f"Error interno procesando resumen para {year}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
