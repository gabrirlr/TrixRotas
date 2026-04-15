from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import date, datetime
from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter
import asyncio

geolocator = Nominatim(user_agent="queonetics-trixlog")

def reverse_geocode(lat: float, lon: float) -> str:
    """Converte coordenadas em endereço legível."""
    try:
        location = geolocator.reverse((lat, lon), language="pt")
        return location.address if location else f"{lat},{lon}"
    except Exception:
        return f"{lat},{lon}"  # fallback: devolve as coordenadas brutas

class RotaCSV(BaseModel):
    model_config = ConfigDict(extra="ignore")

    placa: str = Field(..., min_length=7, max_length=8)
    cliente: str
    latitude: float
    longitude: float
    data_rota: date
    endereco: str = ""  # ← preenchido automaticamente, não precisa vir no CSV

    @field_validator("data_rota", mode="before")
    @classmethod
    def parse_data(cls, v):
        if isinstance(v, str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Formato de data não reconhecido: {v}")
        return v

    @model_validator(mode="after")
    def buscar_endereco(self):
        """Executa reverse geocoding se o endereço não vier no CSV."""
        if not self.endereco:
            self.endereco = reverse_geocode(self.latitude, self.longitude)
        return self