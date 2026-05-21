"""Utilitaires de logging BBS Groove — inspiré de BBS Popcorn."""

import logging
import os
import sys
from pathlib import Path

_logger = logging.getLogger('bbs_groove')
_debug_enabled = False


def setup_logging(debug: bool = False):
    """Configure le logging. Appeler une seule fois au démarrage."""
    global _debug_enabled
    _debug_enabled = debug or os.environ.get('BBS_GROOVE_DEBUG', '0') == '1'

    level = logging.DEBUG if _debug_enabled else logging.INFO
    fmt   = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

    handlers = [logging.StreamHandler(sys.stdout)]

    # Log fichier dans le cache
    try:
        log_dir = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'bbs-groove'
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_dir / 'groove.log'))
    except Exception:
        pass

    logging.basicConfig(level=level, format=fmt, handlers=handlers)
    _logger.setLevel(level)

    if _debug_enabled:
        _logger.info('Mode debug activé')


def log(msg: str, level: str = 'info'):
    getattr(_logger, level.lower(), _logger.info)(msg)
