from langchain_community.tools.amadeus.base import AmadeusBaseTool
from pydantic import BaseModel, Field
from typing import Type
from amadeus import Client


class MyAmadeusFlightSearchTool(AmadeusBaseTool):
    class FlightSearchSchema(BaseModel):
        # explanation of the flight information
        origin: str = Field(description="IATA code of the origin airport (e.g., CTA for Catania).")
        destination: str = Field(description="IATA code of the destination airport (e.g., FCO for Rome).")
        departure_date: str = Field(description="Date of departure in YYYY-MM-DD format.")

    name: str = "flight_search"
    description: str = "Search for flights between two airports."
    args_schema: Type[BaseModel] = FlightSearchSchema

    def _run(self, origin: str, destination: str, departure_date: str, max_flights: int = 2):
        # Use the Amadeus client to search for flights
        client = self.client  # Automatically set up by AmadeusBaseTool

        try:
            # client.shopping.flight_dates.get() Ricerca chepest
            response = client.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=1
            )
            flights = response.data[:max_flights]  # only 2 flights

            return flights
        except Exception as e:
            return {"error": str(e)}

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported yet.")

    def getClient():
        # Create the Amadeus client with your credentials
        amadeus_client = Client(
            client_id="RwZPU0GAxibGNBzOONPR3bPWKsKwkv9s",
            client_secret="exPdhoisqWETlHsU"
        )
        return amadeus_client
