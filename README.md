# Conversational Markov

LLMs don't normally sound like they're talking to you. The LLM in its most 
basic state simply continues the text it's given. LLMs sound like they're
talking to you when they're set up to always complete one side of a
conversation.

Technically, there's nothing stopping you from making a Markov chain generator
do this, too. Train it on prompts and responses delineated by a sentinel token,
and then, during inference, you can make the starting state any given prompt
followed by the sentinel, and it will autocomplete something that sounds like a
fitting response.

This project explores that.  
Now, practically, there are reasons Markov chain generators are _not_ typically
used this way: state size increases linearly with every extra word you want to
be able to prompt the MCG with, and model size correspondingly increases
exponentially. With just a few words and a decent sized corpus, you'll be
running out of memory trying to load the whole thing.

This project is a naïve example of a Markov chain generator set up to respond to
prompts, using an off-the-shelf library. It uses a state size of 3, enough to
allow it to process just the first and last word of a prompt plus the sentinel
token.
