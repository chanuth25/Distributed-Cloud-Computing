from fastapi import FastAPI
import random
app = FastAPI()
@app.get("/lab1/rover/{number}")
def get_rover_commands(number: int):
	commands = ["L", "R", "M"]
	sequence = "".join(random.choice(commands) for _ in range(number))
	return {
		"commands": sequence
	}
