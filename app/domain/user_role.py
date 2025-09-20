from sqlmodel import Field, SQLModel

class User_Role(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    role_name: str = Field(unique=True, index=True)
    description: str