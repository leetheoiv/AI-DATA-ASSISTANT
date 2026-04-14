import sqlalchemy as db
import sqlite3
from sqlalchemy.orm import sessionmaker, declarative_base
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
        self.engine = self.create_db_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_db_engine(self,db_url):
        """
        Create a SQLAlchemy engine for database interaction.
        
        Args:
            db_url (str): The database URL in the format 'dialect+driver://username:password@host:port/database'.
            
        Returns:
            sqlalchemy.engine.base.Engine: A SQLAlchemy engine instance.
        """
        try:
            engine = db.create_engine(db_url,connect_args={"check_same_thread": False})
            return engine.connect()
        except Exception as e:
            print(f"Error creating database engine: {e}")
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
            result = self.conn.execute(db.text(query))
            return result.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            raise

    # Dependency to get a DB session in your routes
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()