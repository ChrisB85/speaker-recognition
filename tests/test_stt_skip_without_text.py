"""STT proxy: speaker recognition can be skipped when the wrapped STT recognized no text."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.stt import SpeechResult, SpeechResultState

from custom_components.speaker_recognition import stt as stt_module

pytestmark = pytest.mark.asyncio


def _entity(skip_without_text: bool):
    entity = stt_module.SpeakerRecognitionSTTEntity.__new__(stt_module.SpeakerRecognitionSTTEntity)
    entity.hass = MagicMock()
    entity.hass.data = {}
    entity.entity_id = "stt.test_speaker_recognition"
    entity._stt_entity_id = "stt.test"
    entity._skip_without_text = skip_without_text
    recognition = MagicMock()
    recognition.async_recognize = AsyncMock(return_value=None)
    entity._main_entry = MagicMock(runtime_data=recognition)
    return entity, recognition


async def _process(entity, text):
    source = MagicMock()

    async def fake_stt(metadata, stream):
        async for _ in stream:
            pass
        return SpeechResult(text, SpeechResultState.SUCCESS if text else SpeechResultState.ERROR)

    source.async_process_audio_stream = fake_stt

    async def audio():
        yield b"\x00\x01" * 100

    with patch.object(stt_module, "async_get_speech_to_text_entity", return_value=source):
        return await entity.async_process_audio_stream(MagicMock(sample_rate=16000), audio())


@pytest.mark.parametrize("text", [None, ""])
async def test_skips_recognition_without_text_when_enabled(text):
    entity, recognition = _entity(skip_without_text=True)
    result = await _process(entity, text)
    recognition.async_recognize.assert_not_called()
    assert result.text == text


async def test_recognizes_when_text_present_and_option_enabled():
    entity, recognition = _entity(skip_without_text=True)
    await _process(entity, "która godzina")
    recognition.async_recognize.assert_awaited_once()


async def test_default_still_recognizes_without_text():
    entity, recognition = _entity(skip_without_text=False)
    await _process(entity, None)
    recognition.async_recognize.assert_awaited_once()
