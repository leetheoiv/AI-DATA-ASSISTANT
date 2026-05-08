import sqlalchemy as sa
import sqlite3 as sqlite
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()
 
 
class DatabaseInteractor:
    """
    A class to handle database interactions using SQLAlchemy.
    """

    def __init__(self, db_url):
        """
        Initialize the DatabaseInteractor with a database URL.
        
        Args:
            db_url (str): The database URL in the format 'dialect+driver://username:password@host:port/database'.
        """
        
        try:
            self.engine = sa.create_engine(db_url, connect_args={"check_same_thread": False})

        except Exception as e:
            print(f"Error initializing database connection: {e}")
            raise
        
    def create_table(self,table_name, columns):
        """
        Create a table in the database if it doesn't exist.
        
        Args:
            table_name (str): The name of the table to create.
            columns (list): A list of dictionaries where keys are column names and values are SQLAlchemy column types.
        """
        metadata = sa.MetaData()
        # Define the table structure
        sa.Table(table_name, metadata, *columns)
        
        # Create it in the DB
        metadata.create_all(self.engine)
        print(f"Table '{table_name}' is ready.")


    def insert_data(self, table_name, data):
        """
        Insert data into a specified table.
        
        Args:
            table_name (str): The name of the table to insert data into.
            data (dict): A dictionary where keys are column names and values are the data to insert.
        """
        try:
            with self.engine.connect() as conn:
                metadata = sa.MetaData()
                table = sa.Table(table_name, metadata, autoload_with=self.engine)
                ins = table.insert().values(**data)
                conn.execute(ins)
                print(f"Data inserted into '{table_name}' successfully.")

                # IMPORTANT: Commit the transaction to persist data
                conn.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")
            raise

    def delete_table(self, table_name):
        """
        Delete a table from the database.
        
        Args:
            table_name (str): The name of the table to delete.
        """
        try:
            metadata = sa.MetaData()
            table = sa.Table(table_name, metadata, autoload_with=self.engine)
            table.drop(self.engine)
            print(f"Table '{table_name}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting table: {e}")
            raise

    def execute_query(self, query):
        """
        Execute a SQL query and return the results.

        Args:
            query (str): The SQL query to execute.
            
        Returns:
            list: A list of dictionaries representing the query results.
        """
        try:

            with self.engine.connect() as conn:
                result = conn.execute(sa.text(query))
                for row in result:
                    print(row)  # Access by attribute or index
        except Exception as e:
            print(f"[Error]: {e}")
            raise
