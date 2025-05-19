import sqlalchemy as sa
import sqlmodel as sm
from tqdm import tqdm

from convmark.globals import GARLIC_OS, OOER_GENERAL
from convmark.my_corpus.models import Message


SOURCE_DB_URL = "sqlite:///home/garlic/parrot/parrot.sqlite3"
DEST_DB_URL = "sqlite:///home/garlic/convmark.sqlite3"


def main() -> list[list[str]]:
	corpus: list[list[str]] = []

	# Get my messages from Parrot's database and convert them to a training set
	# for the conversational model
	with (
		sm.Session(sm.create_engine(SOURCE_DB_URL)) as source,
		sm.Session(sm.create_engine(DEST_DB_URL)) as dest,
	):
		# "Number of my messages in /r/Ooer general"
		stmt_count = sa.select(sa.func.count(sm.col(Message.id))).where(
			sm.col(Message.author_id) == GARLIC_OS
		)
		garlic_corpus_size: int | None = source.execute(stmt_count).scalar()
		assert garlic_corpus_size is not None
		# "For each message of mine in /r/Ooer general, one at a time,"
		stmt_garlic = sm.select(Message).where(
			Message.author_id == GARLIC_OS,
			Message.channel_id == OOER_GENERAL,
		)
		successes = 0
		for i, message_garlic in enumerate(tqdm(
			source.exec(stmt_garlic),
			desc="Messages processed",
			total=garlic_corpus_size,
		)):
			if message_garlic is None:
				print("why is it none")
				continue

			# "The message right before this one in this channel"
			stmt_prev = (
				sm.select(Message)
				.where(
					Message.id < message_garlic.id,
					Message.channel_id == OOER_GENERAL,
				)
				.order_by(sm.col(Message.id).desc())
				.limit(1)
			)
			message_prev = source.exec(stmt_prev).first()

			if message_prev is None:
				continue
			if len(message_garlic.content) == 0:
				print(message_garlic, "how is the message empty")
				continue
			if len(message_prev.content) == 0:
				print(message_garlic, "how is the prev message empty")
				continue

			dest.add(message_garlic)
			dest.add(message_prev)
			if i % 1000 == 0:
				dest.commit()

			successes += 1
		dest.commit()

	print(f"{successes}/{garlic_corpus_size} were salvagable")
	return corpus


if __name__ == "__main__":
	main()
