# api_testing_pytest
Testing an API with PyTest

Assignment:
Test the API endpoint with the following conditions:

1) First task test the following actions:
- Make a new board
- on the new board create a new task/card with desired properties - name, column(status), colour, priority
- try to move the card in a non-existent comlumn - validate the error
- try to change the deadline to an invalid data - validate the error

2) Second task test the following actions:
- create a new initiative on the previously created board
- create a parent/child relationship between the previously created card the new initiative
- move the card in column(Done)
- archive the card
- delete the initiative
