import json
import requests


class TestSecondTask:
    HEADERS = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'apikey': 'your_api_key'
    }
    BOARD_ID = 0
    INITIATIVE_FLOW_ID = 0
    CARD_FLOW_ID = 0
    CARD_INI_ID = 0
    CHILD_CARD_ID = 0
    DONE_COLUMN_ID = 0

    @classmethod
    def set_board_id(cls, value):
        cls.BOARD_ID = value
        return cls.BOARD_ID

    @classmethod
    def set_initiative_flow(cls, value):
        cls.INITIATIVE_FLOW_ID = value
        return cls.INITIATIVE_FLOW_ID

    @classmethod
    def set_card_flow(cls, value):
        cls.CARD_FLOW_ID = value
        return cls.CARD_FLOW_ID

    @classmethod
    def set_card_ini_id(cls, value):
        cls.CARD_INI_ID = value
        return cls.CARD_INI_ID

    @classmethod
    def set_child_card_id(cls, value):
        cls.CHILD_CARD_ID = value
        return cls.CHILD_CARD_ID

    @classmethod
    def set_done_column_id(cls, value):
        cls.DONE_COLUMN_ID = value
        return cls.DONE_COLUMN_ID

    def assign_values(self):
        response_board = json.loads(
            requests.get('url/api/boards', headers=self.HEADERS).text
        )
        board_id = next(filter(lambda x: x.get('name') == "My new board", response_board['data'])).get("board_id")
        self.set_board_id(board_id)

        lanes = json.loads(
            requests.get('url/api/boards' + f"/{board_id}" + '/lanes',
                         headers=self.HEADERS).text
        )
        lane_id = next(filter(lambda x: x.get("name") == "Portfolio Lane", lanes['data'])
                       ).get('lane_id')

        workflows = json.loads(
            requests.get('url/api/boards' + f"/{board_id}" + '/workflows',
                         headers=self.HEADERS).text
        )
        initiative_workflow_id = next(filter(lambda x: x.get("name") == "Initiatives workflow",
                                             workflows['data'])).get("workflow_id")
        self.set_initiative_flow(initiative_workflow_id)
        card_workflow_id = next(filter(lambda x: x.get("name") == "Cards workflow",
                                       workflows['data'])).get("workflow_id")
        self.set_card_flow(card_workflow_id)
        columns = json.loads(
            requests.get('url/api/boards' + f"/{board_id}" + '/columns',
                         headers=self.HEADERS).text
        )
        column_ini_id = next(filter(
            lambda x: x.get("name") == "Requested" and x.get('workflow_id') == initiative_workflow_id,
            columns['data'])).get("column_id")
        column_cards_done = next(filter(
            lambda x: x.get("name") == "Done" and x.get('workflow_id') == card_workflow_id,
            columns['data'])).get("column_id")
        self.set_done_column_id(column_cards_done)
        return lane_id, column_ini_id

    def test_create_initiative(self):
        lane, column = self.assign_values()
        post_data = json.dumps({
            "column_id": column,
            'lane_id': lane,
            'title': 'My new project',
        })
        response = requests.post('url/api/cards',
                                 headers=self.HEADERS, data=post_data)
        card_data = json.loads(response.text)
        self.set_card_ini_id(card_data['data'][0].get('card_id'))
        column_data = json.loads(
            requests.get(
                'url/api/boards/' +
                f'/{self.BOARD_ID}' + '/columns' + f'/{column}', headers=self.HEADERS).text
        )
        assert 200 == response.status_code
        assert 'Requested' == column_data['data'].get('name')

    def test_create_cards_connections(self):
        board_data = json.dumps({'board_ids': self.BOARD_ID})
        cards_response = requests.get('url/api/cards',
                                      headers=self.HEADERS, data=board_data)
        cards = json.loads(cards_response.text)
        child_card_id = next(filter(
            lambda x: x.get("title") == 'My first task', cards['data']['data'])).get("card_id")
        self.set_child_card_id(child_card_id)
        connection_data = json.dumps({
            "links_to_existing_cards_to_add_or_update": [
                {
                    "linked_card_id": self.CHILD_CARD_ID,
                    "link_type": "child",

                },
            ]
        })
        update_response = requests.patch(
            'url/api/cards' + f'/{self.CARD_INI_ID}', headers=self.HEADERS,
            data=connection_data
        )
        update_data = json.loads(update_response.text)
        child = next(filter(lambda x: x.get('title') == 'My new project',
                            update_data['data'])).get('linked_cards')[0]
        assert 200 == update_response.status_code
        assert self.CHILD_CARD_ID == child.get('card_id')

    def test_move_child_card_expect_position_change(self):
        column_data = json.dumps({'column_id': self.DONE_COLUMN_ID})

        update_response = requests.patch(
            'url/api/cards' + f'/{self.CHILD_CARD_ID}', headers=self.HEADERS,
            data=column_data
        )
        update_data = json.loads(update_response.text)

        assert 200 == update_response.status_code
        assert self.DONE_COLUMN_ID == update_data['data'][0].get('column_id')

    def test_parent_location(self):
        parent_data = json.loads(
            requests.get('url/api/cards' + f'/{self.CARD_INI_ID}',
                         headers=self.HEADERS).text
        )
        new_column_id = parent_data['data'].get('column_id')
        column_data = \
            json.loads(
                requests.get('url/api/boards' +
                             f"/{self.BOARD_ID}" +
                             "/columns" + f"/{new_column_id}", headers=self.HEADERS).text
            )
        assert "Requested" != column_data['data'].get("name")

    def test_send_child_to_archive(self):
        data = json.dumps({
            'is_archived': 1,
        })

        update = requests.patch('url/api/cards' + f"/{self.CHILD_CARD_ID}",
                                headers=self.HEADERS, data=data)
        card_data = json.loads(
            requests.get('url/api/cards' + f"/{self.CHILD_CARD_ID}",
                         headers=self.HEADERS).text
        )

        assert update.status_code == 200
        assert 'archived_at' in card_data['data'].keys()

    def test_delete_parent_card(self):
        response = requests.delete(
            'url/api/cards' + f"/{self.CARD_INI_ID}",
            headers=self.HEADERS
        )
        assert 204 == response.status_code
