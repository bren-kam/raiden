# -*- coding: utf-8 -*-
import pytest
import grequests

from raiden.tests.utils.apitestcontext import decode_response
from raiden.utils import netting_channel_to_api_dict
from raiden.tests.utils.transfer import channel


@pytest.mark.parametrize('blockchain_type', ['tester'])
@pytest.mark.parametrize('number_of_nodes', [2])
def test_netting_channel_to_api_dict(raiden_network, tokens_addresses, settle_timeout):
    app0, app1 = raiden_network  # pylint: disable=unbalanced-tuple-unpacking
    channel0 = channel(app0, app1, tokens_addresses[0])

    netting_address = channel0.external_state.netting_channel.address
    netting_channel = app0.raiden.chain.netting_channel(netting_address)

    result = netting_channel_to_api_dict(netting_channel, app0.raiden.address)
    expected_result = {
        "channel_address": '0x' + netting_channel.address.encode('hex'),
        "token_address": '0x' + channel0.token_address.encode('hex'),
        "partner_address": '0x' + app1.raiden.address.encode('hex'),
        "settle_timeout": settle_timeout,
        "balance": channel0.contract_balance,
        "status": "open"
    }
    assert result == expected_result


def test_api_query_channels(api_test_server, api_test_context, api_raiden_service):
    api_test_server.raiden_api = api_raiden_service.api
    responses = grequests.map([grequests.get('http://localhost:5001/api/1/channels')])
    response = responses[0]
    assert response and response.status_code == 200
    assert decode_response(response) == api_test_context.expect_channels()

    api_test_context.make_channel_and_add()
    responses = grequests.map([grequests.get('http://localhost:5001/api/1/channels')])
    response = responses[0]
    assert response.status_code == 200
    assert decode_response(response) == api_test_context.expect_channels()


def test_api_open_channel(api_test_server, api_test_context, api_raiden_service, reveal_timeout):
    api_test_server.raiden_api = api_raiden_service.api
    partner_address = "0x61c808d82a3ac53231750dadc13c777b59310bd9"
    token_address = "0xea674fdde714fd979de3edf0f56aa9716b898ec8"
    settle_timeout = 1650
    channel_data_obj = {
        "partner_address": partner_address,
        "token_address": token_address,
        "settle_timeout": settle_timeout
    }

    responses = grequests.map([grequests.put(
        'http://localhost:5001/api/1/channels',
        data=channel_data_obj
    )])
    response = responses[0]
    assert response and response.status_code == 200
    expected_response = channel_data_obj
    expected_response['reveal_timeout'] = reveal_timeout
    expected_response['balance'] = 0
    expected_response['status'] = 'open'

    assert decode_response(response) == expected_response
