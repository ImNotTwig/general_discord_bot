import discord
from dataclasses import dataclass

@dataclass
class Queue:
    songs: list

def add_to_queue(queue, song):