import json

import requests


class TestFirstTask:
    HEADERS = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'apikey': 'your_api_key'
    }
    MY_BOARD_ID = 0
    WORKPLACES = json.loads(
        requests.get('url/api/workplaces', headers=HEADERS).text
    )
    WORKPLACE_ID = next(
        filter(lambda x: x['name'] == 'Team Boards', WORKPLACES['data'])
    ).get("workspace_id")

    WORKFLOW_CARDS_ID = 0
    NEW_CARD_LANE_ID = 0
    NEW_CARD_COLUMN_ID = 0
    NEW_CARD_ID = 0

    @classmethod
    def set_board_id(cls, value):
        cls.MY_BOARD_ID = value
        return cls.MY_BOARD_ID

    @classmethod
    def set_card_id(cls, value):
        cls.NEW_CARD_ID = value
        return cls.NEW_CARD_ID

    @classmethod
    def set_new_card_column(cls, value):
        cls.NEW_CARD_COLUMN_ID = value
        return cls.NEW_CARD_COLUMN_ID

    @classmethod
    def set_new_card_lane(cls, value):
        cls.NEW_CARD_LANE_ID = value
        return cls.NEW_CARD_LANE_ID

    @classmethod
    def set_cards_workflow(cls, value):
        cls.WORKFLOW_CARDS_ID = value
        return cls.WORKFLOW_CARDS_ID

    def test_board_creation(self):
        data = json.dumps(
            {
                "workspace_id": self.WORKPLACE_ID,
                "name": "My new board",
                "description": "My new board"
            }
        )
        response = requests.post('url/api/boards', headers=self.HEADERS, data=data)
        values = json.loads(response.text)['data']
        self.set_board_id(values.get("board_id"))
        assert response.status_code == 200
        assert values.get("workspace_id") == self.WORKPLACE_ID
        assert values.get("name") == "My new board"
        assert values.get("description") == 'My new board'

    def prepare_test_for_card_creation(self):
        workflows = json.loads(requests.get(
            'url/api/boards/' + f"{self.MY_BOARD_ID}" + '/workflows',
            headers=self.HEADERS).text)
        cards_workflow = next(
            filter(lambda x: x.get("name") == "Cards workflow", workflows['data'])
        ).get('workflow_id')
        self.set_cards_workflow(cards_workflow)

        lanes = json.loads(
            requests.get('url/api/boards/' + f"{self.MY_BOARD_ID}" + '/lanes',
                         headers=self.HEADERS).text
        )

        default_lane_id = next(
            filter(lambda x: x.get("name") == "Default Swimlane", lanes['data'])
        ).get("lane_id")
        columns = json.loads(
            requests.get('url/api/boards/' + f"{self.MY_BOARD_ID}" + '/columns',
                         headers=self.HEADERS).text)
        requested_column_id = next(
            filter(
                lambda x: x.get("workflow_id") == self.WORKFLOW_CARDS_ID and x.get("name") == 'Requested',
                columns['data'])
        ).get("column_id")

        return requested_column_id, default_lane_id

    def test_card_creation(self):
        column, lane = self.prepare_test_for_card_creation()
        self.set_new_card_column(column)
        self.set_new_card_lane(lane)
        post_data = json.dumps(
            {
                "column_id": self.NEW_CARD_COLUMN_ID,
                'lane_id': self.NEW_CARD_LANE_ID,
                'title': 'My first task',
                'color': '00FF5E',
                "priority": 2,
                'description': 'This is my first task'
            }
        )

        response = requests.post('url/api/cards',
                                 headers=self.HEADERS, data=post_data)
        data_response = json.loads(response.text)
        card_id = data_response['data'][0].get('card_id')
        self.set_card_id(card_id)
        assert 200 == response.status_code

    def test_new_card_properties(self):
        card_details = json.loads(
            requests.get('url/api/cards' + f"/{self.NEW_CARD_ID}",
                         headers=self.HEADERS).text
        )
        assert 'My first task' == card_details['data'].get("title")
        assert 'This is my first task' == card_details['data'].get("description")
        assert '00ff5e' == card_details['data'].get("color")
        assert 2 == card_details['data'].get("priority")
        assert self.NEW_CARD_LANE_ID == card_details['data'].get("lane_id")
        assert self.NEW_CARD_COLUMN_ID == card_details['data'].get("column_id")

    def test_move_card_to_unexisting_column(self):
        move_data = json.dumps({"column_id": 999})
        response_change = requests.patch('url/api/cards/' + f'{self.NEW_CARD_ID}',
                                         headers=self.HEADERS,
                                         data=move_data)
        details = json.loads(response_change.text)
        assert 400 == response_change.status_code
        assert "A column with id 999 does not exist." == details['error']['message']

    def test_create_card_with_invalid_deadline(self):
        deadline_data = json.dumps(
            {
                "column_id": self.NEW_CARD_COLUMN_ID,
                'lane_id': self.NEW_CARD_LANE_ID,
                'title': 'Test Dealine',
                'color': '00FF5E',
                "priority": 2,
                "deadline": "1969-05-19T08:09:18Z"
            }
        )
        response_deadline = requests.post('api/api/cards',
                                          headers=self.HEADERS,
                                          data=deadline_data)
        details = json.loads(response_deadline.text)
        assert 400 == response_deadline.status_code
        assert "The parameters in the request body did not pass validation." == details['error']['message']
        assert "The date and time must be after 1970-01-01 00:00:00." == details['error']['details']['deadline'][0]
