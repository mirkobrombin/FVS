# FVS
File Versioning System with hash comparison and data storage to create unlinked states that can be deleted

> ⚠️ This is a work in progress.

### Usage

```python
from fvs import FVSRepo

# create a new repo or point to an existing one
repo = FVSRepo("just/one/path")

# add some new files
with open("test/hello.txt", "w") as f:
    f.write("Hello world!")
    
with open("test/ciao.txt", "w") as f:
    f.write("Ciao!")

# commit the changes
repo.commit("My first state!")

# add some more files
with open("test/test.txt", "w") as f:
    f.write("Hello world again!")

with open("test/test.ignore", "w") as f:
    f.write("This time nobody will see this!")

# commit the changes ignoring files with .ignore extension
repo.commit("My second state!", ignore=["*.ignore"])
```

### What is working
- creating new repository
- committing changes / creating states
- patterns to ignore files
- storing data with deduplication

### What is not working yet
- restoring states
- deleting states
