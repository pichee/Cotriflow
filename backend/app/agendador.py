from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

from .controle import iniciaPredicao

logger = logging.getLogger(__name__)


class AgendadorPredicao:
    """Agendador que dispara iniciaPredicao() diariamente às 12:00."""

    def __init__(self, horario: str = "12:00") -> None:
        self.horario = horario
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._ultima_execucao_data: str | None = None

    def executar_agora(self):
        return iniciaPredicao()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            agora = datetime.now()
            hoje_str = agora.strftime("%Y-%m-%d")
            hora_str = agora.strftime("%H:%M")
            if hora_str == self.horario and self._ultima_execucao_data != hoje_str:
                try:
                    iniciaPredicao()
                    self._ultima_execucao_data = hoje_str
                except Exception as exc:
                    logger.error("Erro na execução agendada de iniciaPredicao: %s", exc)
            self._stop_event.wait(30)

    def iniciar(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def parar(self) -> None:
        self._stop_event.set()


agendador = AgendadorPredicao(horario="12:00")
