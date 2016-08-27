# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-
import pytest
import guisupport as acylgui


@pytest.fixture()
def handler():
	def action():
		action.runned = True

	action.runned = False
	return acylgui.ActionHandler(action)


def test_blocked_run(handler):
	handler.set_state(False)
	handler.run()
	assert not handler.action.runned


def test_allowed_run(handler):
	handler.set_state(True)
	handler.run()
	assert handler.action.runned


def test_forced_run(handler):
	handler.set_state(False)
	handler.run(forced=True)
	assert handler.action.runned
