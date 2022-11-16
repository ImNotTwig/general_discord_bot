from dataclasses import dataclass
import toml
import os

@dataclass
class Tokens:
    discord_token: str
    genius_token: str
    spotify_id: str
    spotify_secret: str


@dataclass
class LevelSystem:
    levels_on: bool
    xp_per_message: list[int]
    cooldown_in_seconds: int


@dataclass
class SpamSettings:
    antispam: bool
    spam_count: int


@dataclass
class Config:
    tokens: Tokens
    spam_settings: SpamSettings
    level_system: LevelSystem
    prefix: str

with open('config.toml') as config_file:
    config = toml.load(config_file)

if not config['tokens']['discord_token']:
    config['tokens']['discord_token'] = os.getenv('discord_token')

tokens = Tokens(
    discord_token=config['tokens']['discord_token'],
    genius_token=config['tokens']['genius_token'],
    spotify_id=config['tokens']['spotify_id'],
    spotify_secret=config['tokens']['spotify_secret'],
)

level_system = LevelSystem(
    levels_on=config['level_system']['levels_on'],
    xp_per_message=config['level_system']['xp_per_message'],
    cooldown_in_seconds=config['level_system']['cooldown_in_seconds'],
)

spam_settings = SpamSettings(
    antispam=config['spam_settings']['antispam'],
    spam_count=config['spam_settings']['spam_count'],
)

prefix = config['prefix']

config = Config(
    tokens=tokens,
    level_system=level_system,
    spam_settings=spam_settings,
    prefix=prefix,
)
