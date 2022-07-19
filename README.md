# FVS
File Versioning System with hash comparison and data storage to create unlinked 
states that can be deleted

> ⚠️ This is currently a Beta.

### Why FVS?
The main reason for this project is for the purpose of personal knowledge and 
understanding of the versioning system. The second reason is to make a simple
and easy-to-implement versioning system for [Bottles](https://github.com/bottlesdevs/Bottles).

There are plenty of other versioning systems out there, but all of these 
provide features that I wouldn't need in my projects. The purpose of FVS is to 
always remain as clear and simple as possible, providing only the functionality 
of organizing file versions into states, ie recovery points that take advantage 
of deduplication to minimize space consumption.

### Dependencies
FVS only need the `orjson` python package.

### CLI usage
```bash
> mkdir repo ; cd repo
> fvs init  # or fvs init --path <path>
Initialized FVS repository in /your/location/repo

> touch hello.txt
> fvs commit -m "First state"  # -i=<pattern> -i=<pattern2> to ignore files
Committing...
Committed state 0

> echo "Hello world!" >> hello.txt
> fvs commit -m "Second state"
Committing...
Committed state 1

> fvs states
-   0 First state
- ➔ 1 Second state

> fvs restore 0
Restored state 0

> fvs active
Active state is 0
```

### Lib usage

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

# restore the state 1
repo.restore_state(1)
```
