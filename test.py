import logging
from fvs.repo import FVSRepo

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    repo = FVSRepo("test")

    # First commit
    with open("test/hello.txt", "w") as f:
        f.write("Hello world!")  # will be placed in data/h

    with open("test/hello2.txt", "w") as f:
        f.write("Hello world 2!")  # will be placed in data/h
    
    with open("test/ciao.txt", "w") as f:
        f.write("Ciao!")  # will be placed in data/c
    
    with open("test/*&^.txt", "w") as f:
        f.write("*&^ bip bop!")  # will be placed in data/-

    repo.commit("My first state!")

    # Second commit
    with open("test/test.txt", "w") as f:
        f.write("Hello world again!")  # will be placed in data/t

    with open("test/test.exclude", "w") as f:
        f.write("Hello world again but this time doesn't matter!")  # will be excluded by the above 'ignore' pattern

    repo.commit("Another state =)", ignore=["*.exclude"])



