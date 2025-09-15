"""
Temperature Conversion MCP Server
Provides temperature conversion capabilities through MCP HTTP protocol.
"""
import click
import logging
from typing import Union
from pydantic import BaseModel, Field, Validator
from mcp.server.fastmcp import FastMCP

@click.command()
@click.option("--port", default=8001, help="Port to run the server to")
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--log-level", default="INFO", help="Logging level")

def main(port: int, host: str, log_level: str) -> None:
    """Launch the temperature conversion MCP server"""

    # config logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting temperature conversion MCP server on {host}:{port}")

    # create FastMCP server with streamable  HTTP transport
    mcp = FastMCP(
        "temperature_converter",
        host=host,
        port=port,
        stateless_http=True # Enable stateless HTTP transport
        )

    # Input/Output models for type safety and validation
    class TemperatureInput(BaseModel):
        """Input model for temperature conversio with validation"""
        temperature: float = Field(..., description="Temperature value to convert")

        @validator("temperature")
        def validate_temperature_range(cls, v):
            """Validate temperature range between -273.15 and 100000"""
            if v < -273.15 or v > 100000:
                raise ValueError("Temperature must be between -273.15 and 100000")
            return v
    
    class TemperatureOutput(BaseModel):
        """Output model for temperature conversion results"""
        original_value: float = Field(..., description="Original temperature value")
        original_scale: str = Field(..., description="Original temperature scale (C, F, K)")
        converted_value: float = Field(..., description="Converted temperature value")
        converted_scale: str = Field(..., description="Converted temperature scale (C, F, K)")
        formula: str = Field(..., description="Conversion formula used")

    # core conversion functions(business logic)
    def celcius_to_fahrenheit_calc(celsius: float) -> float:
        """Convert Celsius to Fahrenheit using the formula: (C * 9/5) + 32"""
        return (celsius * 9/5) + 32

    def fahrenheit_to_celcius_calc(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius using the formula: (F - 32) * 5/9"""
        return (fahrenheit - 32) * 5/9

    def celcius_to_kelvin_calc(celsius: float) -> float:
        """Convert Celsius to Kelvin using the formula: C + 273.15"""
        return celsius + 273.15

    def kelvin_to_celcius_calc(kelvin: float) -> float:
        """Convert Kelvin to Celsius using the formula: K - 273.15"""
        return kelvin - 273.15

    def fahrenheit_to_kelvin_calc(fahrenheit: float) -> float:
        """Convert Fahrenheit to Kelvin using the formula: (F - 32) * 5/9 + 273.15"""
        return (fahrenheit - 32) * 5/9 + 273.15

    def kelvin_to_fahrenheit_calc(kelvin: float) -> float:
        """Convert Kelvin to Fahrenheit using the formula: (K - 273.15) * 9/5 + 32"""
        return (kelvin - 273.15) * 9/5 + 32

    # MCP tool Registrations - These become available to the client

    @mcp.tool(
        description="Convert temperature from Celsius to Fahrenheit",
        title="celsius to fahrenheit convertor"
    )
    async def celsius_to_fahrenheit(params: TemperatureInput) -> TemperatureOutput:
        """ Convert celsius to fahrenheit with validation"""
        converted = celsius_to_fahrenheit_calc(params.temperature)
        return TemperatureOutput(
            original_value=params.temperature,
            original_scale="C",
            converted_value=converted,
            converted_scale="F",
            formula="F = (C * 9/5) + 32"
        )
    
    @mcp.tool(
        description="Convert temperature from Fahrenheit to Celsius",
        title="fahrenheit to celsius convertor"
    )
    async def fahrenheit_to_celsius(params: TemperatureInput) -> TemperatureOutput:
        """ Convert fahrenheit to celsius with validation"""
        # Additional validation for fahrenheit absolute zero
        if params.temperature < -459.67: # Below absolute zero fahrenheit
            raise ValueError("Temperature cannot be below absolute zero Fahrenheit")
        
        converted = fahrenheit_to_celsius_calc(params.temperature)
        return TemperatureOutput(
            original_value=params.temperature,
            original_scale="F",
            converted_value=converted,
            converted_scale="C",
            formula="C = (F - 32) * 5/9"
        )
    
    @mcp.tool(
        description="Convert temperature from Celsius to Kelvin",
        title="celsius to kelvin convertor"
    )
    async def celsius_to_kelvin(params: TemperatureInput) -> TemperatureOutput:
        """ Convert celsius to kelvin with validation"""
        converted = celcius_to_kelvin_calc(params.temperature)
        return TemperatureOutput(
            original_value=params.temperature,
            original_scale="C",
            converted_value=converted,
            converted_scale="K",
            formula="K = C + 273.15"
        )
    
    @mcp.tool(
        description="Convert temperature from Kelvin to Celsius",
        title="kelvin to celsius convertor"
    )
    async def kelvin_to_celsius(params: TemperatureInput) -> TemperatureOutput:
        """ Convert kelvin to celsius with validation"""
        # kelvin cannot be below absolute zero
        if params.temperature < 0:
            raise ValueError("Temperature cannot be below absolute zero Kelvin")
        converted = kelvin_to_celcius_calc(params.temperature)
        return TemperatureOutput(
            original_value=params.temperature,
            original_scale="K",
            converted_value=converted,
            converted_scale="C",
            formula="C = K - 273.15"
        )

    @mcp.tool(
        description="Convert temperature from Fahrenheit to Kelvin",
        title="fahrenheit to kelvin convertor"
    )
    async def fahrenheit_to_kelvin(params: TemperatureInput) -> TemperatureOutput:
        """ Convert fahrenheit to kelvin with validation"""
        # fahrenheit cannot be below absolute zero
        if params.temperature < -459.67:
            raise ValueError("Temperature cannot be below absolute zero Fahrenheit")
        converted = fahrenheit_to_kelvin_calc(params.temperature)
        return TemperatureOutput(
            original_value=params.temperature,
            original_scale="F",
            converted_value=converted,
            converted_scale="K",
            formula="K = (F - 32) * 5/9 + 273.15"
        )
    
    @mcp.tool(
        description="Convert temperature from Kelvin to Fahrenheit",
        title="kelvin to fahrenheit convertor"
    )
    async def kelvin_to_fahrenheit(params: TemperatureInput) -> TemperatureOutput:
        """ Convert kelvin to fahrenheit with validation"""
        # kelvin cannot be below absolute zero
        if params.temperature < 0:
            raise ValueError("Temperature cannot be below absolute zero Kelvin")
        converted = kelvin_to_fahrenheit_calc(params.temperature)
        return TemperatureOutput(
            original_value=params.temperature,
            original_scale="K",
            converted_value=converted,
            converted_scale="F",
            formula="F = (K - 273.15) * 9/5 + 32"
        )


if __name__ == "__main__":
    logger.info("Starting temperature conversion MCP server (HTTP transport)")
    main()