import json
from pathlib import Path

import markovify
import sqlalchemy as sa
import sqlmodel as sm
from tqdm import tqdm

import convmark.convmark as c
from convmark.my_corpus.globals import GARLIC_OS, OOER_GENERAL
from convmark.my_corpus.models import Message


DB_URL = (
	"sqlite:///G:/Garlic/Documents/Code/Python/"
	"conversational-markov/convmark.sqlite3"
)
SEQUENCES_PATH = Path("convmark/my_corpus/sequences")


def remove_log(corpus: list[list[str]], state: markovify.chain.State) -> None:
	for i, log in enumerate(corpus):
		if log[0] == state[0] and log[1] == state[1]:
			del corpus[i]


def insert_sequence(corpus: list[list[str]], sequence_path: Path) -> None:
	prompt = ("", "")
	with sequence_path.open(encoding="utf-8") as fin:
		for line in fin:
			if len(line.strip()) == 0:
				continue
			corpus.append([*prompt, c.RESPONSE, line])
			prompt = c.encode_prompt(line)


def try_del_val(corpus: list[list[str]], val: list[str]) -> None:
	try:
		del corpus[corpus.index(val)]
	except ValueError:
		pass


def perform_manual_corrections(corpus: list[list[str]]) -> None:
	# in place
	try_del_val(corpus, ["plants", c.WILDCARD, c.RESPONSE, "shrimp"])
	try_del_val(corpus, ["tendrils", c.WILDCARD, c.RESPONSE, "plants"])
	try_del_val(corpus, ["shrimp", c.WILDCARD, c.RESPONSE, "tendrils"])
	try_del_val(corpus, ["🌱", c.WILDCARD, c.RESPONSE, "🦐"])
	try_del_val(corpus, ["<:tendrils:585579718737395732>", c.WILDCARD, c.RESPONSE, "🌱"])
	try_del_val(corpus, ["🦐", c.WILDCARD, c.RESPONSE, "<:tendrils:585579718737395732>"])
	for path in SEQUENCES_PATH.glob("*.txt"):
		insert_sequence(corpus, path)
	corpus.append(["some", c.WILDCARD, c.RESPONSE, "body"])
	corpus.append(["body", c.WILDCARD, c.RESPONSE, "once"])
	corpus.append(["once", c.WILDCARD, c.RESPONSE, "told me the world was gonna roll me"])


def generate_corpus() -> list[list[str]]:
	corpus: list[list[str]] = []

	# Get my messages from Parrot's database and convert them to a training set
	# for the conversational model
	with sm.Session(sm.create_engine(DB_URL)) as session:
		# "Number of my messages in /r/Ooer general"
		stmt_count = sa.select(sa.func.count(sm.col(Message.id))).where(
			sm.col(Message.author_id) == GARLIC_OS
		)
		garlic_corpus_size: int | None = session.execute(stmt_count).scalar()
		assert garlic_corpus_size is not None
		# "For each message of mine in /r/Ooer general, one at a time,"
		stmt_garlic = sm.select(Message).where(
			Message.author_id == GARLIC_OS,
			Message.channel_id == OOER_GENERAL,
		)
		successes = 0
		for message_garlic in tqdm(
			session.exec(stmt_garlic),
			desc="Messages processed",
			total=garlic_corpus_size,
		):
			if message_garlic is None:
				print("why is it none")
				continue

			# "The message right before this one in this channel"
			stmt_prev = (
				sm.select(Message.content)
				.where(
					Message.id < message_garlic.id,
					Message.channel_id == OOER_GENERAL,
				)
				.order_by(sm.col(Message.id).desc())
				.limit(1)
			)
			message_prev_content = session.exec(stmt_prev).first()

			if message_prev_content is None:
				continue
			if len(message_garlic.content) == 0:
				print(message_garlic, "how is the message empty")
				continue
			if len(message_prev_content) == 0:
				print(message_garlic, "how is the prev message empty")
				continue

			garlic_words = message_garlic.content.split()
			first, last = c.encode_prompt(message_prev_content)
			log = []
			if len(first) > 0:
				log.append(first)
			if len(last) > 0:
				log.append(last)
			log.append(c.RESPONSE)
			log += garlic_words
			corpus.append(log)

			successes += 1

	print(f"{successes}/{garlic_corpus_size} were salvagable")
	return corpus


def main() -> None:
	# corpus = generate_corpus()
	# with open("convmark.json", "w") as fout:
	# 	json.dump(corpus, fout)

	# with open("convmark.json") as fin:
	# 	corpus: list[list[str]] = json.load(fin)

	# perform_manual_corrections(corpus)

	# with open("convmark.json", "w") as fout:
	# 	json.dump(corpus, fout)

	with open("convmark.json") as fin:
		corpus: list[list[str]] = json.load(fin)

	model = c.ConvMark(corpus)

	try:
		while True:
			prompt = input("> ")
			print(model.respond(prompt))
	except KeyboardInterrupt:
		pass


if __name__ == "__main__":
	main()
