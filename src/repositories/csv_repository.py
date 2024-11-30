"""
CSV-based repository implementation with thread-safe file handling.
"""
import csv
import asyncio
from typing import Generic, TypeVar, Optional, List, Any, Type, Dict
from pathlib import Path
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np
from pydantic import BaseModel

from src.repositories.base_repository import Repository, TimeRangeRepository
from src.utils.exceptions import StorageError
from config.settings import get_settings

settings = get_settings()

T = TypeVar("T", bound=BaseModel)


def clean_nan_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert NaN values to None."""
    return {
        key: None if pd.isna(value) else value
        for key, value in data.items()
    }


class CSVRepository(Repository[T], Generic[T]):
    """Base CSV repository implementation."""
    
    def __init__(
        self,
        file_path: Path,
        model_class: Type[T],
        key_field: str
    ) -> None:
        """Initialize CSV repository."""
        super().__init__()
        self.file_path = file_path
        self.model_class = model_class
        self.key_field = key_field
        self._lock = asyncio.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create CSV file if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            fields = list(self.model_class.model_fields.keys())
            df = pd.DataFrame(columns=fields)
            df.to_csv(self.file_path, index=False)

    async def _read_df(self) -> pd.DataFrame:
        """Read CSV into DataFrame with proper error handling."""
        try:
            async with self._lock:
                # Read with string type for key field and handle NaN values
                df = pd.read_csv(
                    self.file_path,
                    dtype={self.key_field: str},
                    keep_default_na=False,
                    na_values=['']
                )
                if df.empty:
                    return pd.DataFrame(columns=list(self.model_class.model_fields.keys()))
                # Ensure key field is properly formatted
                if self.key_field in df.columns:
                    df[self.key_field] = df[self.key_field].astype(str).str.zfill(10)
                return df
        except Exception as e:
            raise StorageError(f"Failed to read CSV: {str(e)}") from e

    async def _write_df(self, df: pd.DataFrame) -> None:
        """Write DataFrame to CSV with proper error handling."""
        try:
            async with self._lock:
                # Convert None to empty string to avoid NaN
                df = df.replace({np.nan: None})
                df.to_csv(self.file_path, index=False, na_rep='')
        except Exception as e:
            raise StorageError(f"Failed to write CSV: {str(e)}") from e

    def _model_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert model to dictionary, handling nested models and enums."""
        data = entity.model_dump()
        # Convert any nested Pydantic models or enums to their string representation
        for key, value in data.items():
            if isinstance(value, BaseModel):
                data[key] = value.model_dump_json()
            elif isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, datetime):
                data[key] = value.isoformat() if value is not None else None
            elif key == self.key_field and value is not None:
                data[key] = str(value).zfill(10)
            elif value is None:
                data[key] = ''  # Use empty string for None values
        return data

    async def add(self, entity: T) -> T:
        """Add new entity to CSV."""
        df = await self._read_df()
        
        key_value = str(getattr(entity, self.key_field)).zfill(10)
        # Check for existing entity
        if self.key_field in df.columns and not df.empty:
            if df[df[self.key_field] == key_value].shape[0] > 0:
                raise StorageError(f"Entity with {self.key_field}={key_value} already exists")
        
        # Convert entity to dictionary and add as new row
        new_data = self._model_to_dict(entity)
        new_df = pd.DataFrame([new_data])
        
        # Ensure column order matches
        if not df.empty:
            new_df = new_df[df.columns]
        
        df = pd.concat([df, new_df], ignore_index=True)
        await self._write_df(df)
        return entity

    async def get(self, id_: Any) -> Optional[T]:
        """Get entity by ID."""
        df = await self._read_df()
        
        if df.empty:
            return None
        
        # Ensure ID is properly formatted for comparison
        id_formatted = str(id_).zfill(10)
        
        # Find matching row
        row = df[df[self.key_field] == id_formatted]
        if row.empty:
            return None
        
        try:
            # Convert row to dict and clean NaN values
            data = clean_nan_values(row.iloc[0].to_dict())
            
            # Convert types as needed
            for field_name, field_info in self.model_class.model_fields.items():
                if field_info.annotation == datetime and isinstance(data.get(field_name), str):
                    data[field_name] = pd.to_datetime(data[field_name]) if data[field_name] else None
                elif field_name == self.key_field and data.get(field_name):
                    data[field_name] = str(data[field_name]).zfill(10)
            
            return self.model_class(**data)
        except Exception as e:
            raise StorageError(f"Failed to convert data to model: {str(e)}") from e

    async def get_all(self) -> List[T]:
        """Get all entities."""
        df = await self._read_df()
        if df.empty:
            return []
        
        try:
            entities = []
            for _, row in df.iterrows():
                data = clean_nan_values(row.to_dict())
                for field_name, field_info in self.model_class.model_fields.items():
                    if field_info.annotation == datetime and isinstance(data.get(field_name), str):
                        data[field_name] = pd.to_datetime(data[field_name]) if data[field_name] else None
                    elif field_name == self.key_field and data.get(field_name):
                        data[field_name] = str(data[field_name]).zfill(10)
                entities.append(self.model_class(**data))
            return entities
        except Exception as e:
            raise StorageError(f"Failed to convert data to models: {str(e)}") from e

    async def add_many(self, entities: List[T]) -> List[T]:
        """Add multiple entities to CSV."""
        if not entities:
            return []
            
        df = await self._read_df()
        
        # Convert entities to DataFrames for efficient comparison
        new_dicts = [self._model_to_dict(entity) for entity in entities]
        new_df = pd.DataFrame(new_dicts)
        
        # Check for duplicates
        if self.key_field in df.columns and not df.empty:
            key_values = set(df[self.key_field].values)
            new_keys = set(new_df[self.key_field].values)
            if key_values.intersection(new_keys):
                raise StorageError("One or more entities already exist")
        
        # Ensure column order matches
        if not df.empty:
            new_df = new_df[df.columns]
        
        # Concatenate and save
        df = pd.concat([df, new_df], ignore_index=True)
        await self._write_df(df)
        return entities

    async def update(self, entity: T) -> Optional[T]:
        """Update existing entity."""
        df = await self._read_df()
        
        if df.empty:
            return None
        
        key_value = str(getattr(entity, self.key_field)).zfill(10)
        mask = df[self.key_field] == key_value
        if not df[mask].shape[0]:
            return None
        
        # Update row with new data
        new_data = self._model_to_dict(entity)
        for column in df.columns:
            if column in new_data:
                df.loc[mask, column] = new_data[column]
        
        await self._write_df(df)
        return entity

    async def delete(self, id_: Any) -> bool:
        """Delete entity by ID."""
        df = await self._read_df()
        
        if df.empty:
            return False
        
        id_formatted = str(id_).zfill(10)
        mask = df[self.key_field] == id_formatted
        if not df[mask].shape[0]:
            return False
        
        df = df[~mask]
        await self._write_df(df)
        return True

    async def exists(self, id_: Any) -> bool:
        """Check if entity exists."""
        df = await self._read_df()
        if df.empty:
            return False
        
        id_formatted = str(id_).zfill(10)
        return df[df[self.key_field] == id_formatted].shape[0] > 0

class TimeRangeCSVRepository(CSVRepository[T], TimeRangeRepository[T], Generic[T]):
    """CSV repository with time-range query support."""
    
    def __init__(
        self,
        file_path: Path,
        model_class: Type[T],
        key_field: str,
        date_field: str
    ) -> None:
        """Initialize time-range CSV repository."""
        super().__init__(file_path, model_class, key_field)
        self.date_field = date_field

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[T]:
        """Get entities within date range."""
        df = await self._read_df()
        
        if df.empty:
            return []
        
        try:
            # Convert date column to datetime
            df[self.date_field] = pd.to_datetime(df[self.date_field])
            
            # Filter by date range
            mask = (df[self.date_field] >= start_date) & (df[self.date_field] <= end_date)
            filtered_df = df[mask]
            
            # Convert to models
            entities = []
            for _, row in filtered_df.iterrows():
                data = row.to_dict()
                for field_name, field_info in self.model_class.model_fields.items():
                    if field_info.annotation == datetime and isinstance(data.get(field_name), str):
                        data[field_name] = pd.to_datetime(data[field_name])
                    elif field_name == self.key_field and data.get(field_name):
                        data[field_name] = str(data[field_name]).zfill(10)
                entities.append(self.model_class(**data))
            return entities
        except Exception as e:
            raise StorageError(f"Failed to process date range query: {str(e)}") from e