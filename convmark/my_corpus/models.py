from sqlmodel import Field, SQLModel


Snowflake = int


class Message(SQLModel, table=True):
	id: Snowflake = Field(primary_key=True)
	content: str
	author_id: Snowflake = Field(foreign_key="user.id")
	channel_id: Snowflake = Field(foreign_key="channel.id")
	guild_id: Snowflake = Field(foreign_key="guild.id")
