<template>
  <div class="TicTacToe">
    <div class="stat">
      <div class="title">
        Победы в состязаниях: X <span>{{ victories.X }}</span> ˑ O <span>{{ victories.O }}</span>
      </div>

      <div class="description">
        Количество тренировок и состязаний: {{ trainingGames + duelGames }}
      </div>

      <div class="timer">
        Время обучения в секундах: {{ timer }}
      </div>
    </div>

    <div class="fields">
      <div
        v-for="(agent, agentIndex) in agents.X.concat(agents.O)"
        :key="agentIndex"
        class="field"
      >
        <div
          v-for="(sign, cellIndex) in agent.field"
          :key="`${agentIndex}:${cellIndex}`"
          :class="['cell', {
            sign,
            alive: agent.isAlive,
            victory: agent.isVictory,
          }]"
          @click="setSign(agent, cellIndex)"
        >
          {{ sign }}
          <!--{{ agent.rewards[cellIndex].toFixed(1) }}-->
        </div>

        <div class="caption">
          Поле игрока: {{ agent.sign }}
        </div>
      </div>
    </div>

    <div class="duel-field">
      <div
        v-for="(sign, cellIndex) in duel.field"
        :key="cellIndex"
        :class="['cell', sign, { victory: victoriesStatus[sign] }]"
      >
        {{ sign }}
      </div>

      <div class="caption">
        Поле для состязаний
      </div>
    </div>

    <div class="fields-description">
      <div>Первая игра - игроки на своих полях, вторая игра - состязание.</div>
      <div>Подсветка золотистым - победа. Цель обучения - сводить игру в ничью.</div>
    </div>

    <div class="ai-vs-human-container">
      <div class="caption">
        Человек против AI
      </div>

      <div class="field">
        <div
          v-for="(sign, cellIndex) in AIvsHuman.field"
          :key="cellIndex"
          :class="['cell', { victory: victoriesStatus[sign] }]"
          @click="setHumanSign(cellIndex)"
        >
          {{ sign }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// todo 3 Этап. Поле для игры с человеком. Обучение во время игры не останавливается.

import * as tf from '@tensorflow/tfjs';
import { victoryCheckGroups as hasVictory } from './utils';

const isAutomatic = true;
const isDelay = false;

export default {
  name: 'TicTacToe',

  data() {
    return {
      modelX: tf.sequential(),
      modelO: tf.sequential(),
      trainingCount: { X: 0, O: 0 },
      training: {
        X: { inputs: [], labels: [] },
        O: { inputs: [], labels: [] },
      },
      agents: { X: [], O: [] },
      victories: { X: 0, O: 0 },
      victoriesStatus: { X: false, O: false },

      fieldSize: 9,
      step: 1,
      trainingGames: 1,

      isDuel: false,
      duel: { // Настраивается в startDuel
        step: 1,
        field: [
          '', '', '',
          '', '', '',
          '', '', '',
        ],
      },
      duelGames: 1,

      timerStart: 0,
      timer: 0,

      AIvsHuman: {
        step: 1,
        rewards: [
          0.1, 0.1, 0.1,
          0.1, 0.1, 0.1,
          0.1, 0.1, 0.1,
        ],
        field: [
          '', '', '',
          '', '', '',
          '', '', '',
        ],
      },
    };
  },

  async mounted() {
    this.setupModel({ model: this.modelX });
    this.setupModel({ model: this.modelO });

    this.agentsSetting({ sign: 'X' });
    this.agentsSetting({ sign: 'O' });

    if (isAutomatic) {
      this.gameLoop();
    }

    this.timerStart = performance.now();
    this.setTimer();
  },

  methods: {
    setupModel({ model }) {
      model.add(tf.layers.dense({
        // +1 - Количество ходов.
        inputShape: [this.fieldSize + 1],
        activation: 'sigmoid',
        units: 32,
      }));

      model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: 24,
      }));

      model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: this.fieldSize,
      }));

      model.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });
    },

    agentsSetting({ sign }) {
      this.agents[sign] = [
        {
          sign,
          isAlive: true,
          isVictory: false,
          rewards: [
            0.1, 0.1, 0.1,
            0.1, 0.1, 0.1,
            0.1, 0.1, 0.1,
          ],
          field: [
            '', '', '',
            '', '', '',
            '', '', '',
          ],
        },
      ];
    },

    async gameLoop() {
      if (this.isDuel) {
        await this.startDuel();
        this.duelGames += 1;
      } else {
        this.isDuel = this.trainingGames % this.fieldSize === 0;
        this.trainingGames += 1;

        await this.startTraining();
      }

      if (isDelay) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      this.gameLoop();
    },

    async startDuel() {
      await new Promise((resolve) => {
        const agents = this.agents.X.filter(({ isAlive }) => isAlive);
        let count = agents.length;

        if (agents.length > 0) {
          agents.forEach(async (agent) => {
            await this.modelPredict({ model: this.modelX, agent });
            count -= 1;

            if (count === 0) {
              resolve();
            }
          });
        } else {
          resolve();
        }
      });

      await new Promise((resolve) => {
        const agents = this.agents.O.filter(({ isAlive }) => isAlive);
        let count = agents.length;

        if (agents.length > 0) {
          agents.forEach(async (agent) => {
            await this.modelPredict({ model: this.modelO, agent });
            count -= 1;

            if (count === 0) {
              resolve();
            }
          });
        } else {
          resolve();
        }
      });

      if (this.duel.step === this.fieldSize) {
        await Promise.all([
          this.modelFit({ model: this.modelX, sign: 'X' }),
          this.modelFit({ model: this.modelO, sign: 'O' }),
        ]);

        this.isDuel = false;

        this.duel = {
          step: 1,
          field: [
            '', '', '',
            '', '', '',
            '', '', '',
          ],
        };
      } else {
        this.duel.step += 1;
      }
    },

    async startTraining() {
      await Promise.all(this.agents.X.filter(({ isAlive }) => isAlive)
        .map((agent) => this.modelPredict({ model: this.modelX, agent }))
        .concat(this.agents.O.filter(({ isAlive }) => isAlive)
          .map((agent) => this.modelPredict({ model: this.modelO, agent }))));

      if (this.step === this.fieldSize) {
        await Promise.all([
          this.modelFit({ model: this.modelX, sign: 'X' }),
          this.modelFit({ model: this.modelO, sign: 'O' }),
        ]);

        this.step = 1;
      } else {
        this.step += 1;
      }
    },

    /* eslint-disable no-confusing-arrow */
    async modelPredict({ model, agent }) {
      const step = this.isDuel ? this.duel.step : this.step;
      let stepInput;

      if (step <= 3) {
        stepInput = step / 3;
      } else {
        stepInput = 1 - (step / this.fieldSize);
      }

      const predictions = await model.predict(tf.tensor2d([agent.rewards.concat([stepInput])])).data();
      const cellIndex = predictions.indexOf(Math.max(...predictions));

      const { sign } = agent;
      const field = this.isDuel ? this.duel.field : agent.field;

      if (field[cellIndex].length === 0) {
        field.splice(cellIndex, 1, sign);
        agent.rewards = agent.rewards.map((weight) => weight + 0.1);

        const isWinner = this.determineWinner({ field, sign });

        if (isWinner) {
          agent.isAlive = false;
          agent.isVictory = true;
          agent.rewards[cellIndex] = 0.99;

          this.saveTraining({
            input: field.map((cell) => cell === sign ? 0.9 : 0.1).concat([stepInput]),
            label: agent.rewards,
            sign,
          });

          if (this.isDuel) {
            this.victories[sign] += 1;
            this.victoriesStatus[sign] = true;
          }
        } else {
          agent.rewards[cellIndex] = 0.5;

          this.saveTraining({
            input: field.map((cell) => cell === sign ? 0.5 : 0.05).concat([stepInput]),
            label: agent.rewards,
            sign,
          });
        }
      } else {
        agent.isAlive = false;
        agent.rewards[cellIndex] = 0.01;

        this.saveTraining({
          input: field.map((cell) => cell.length === 0 ? 0.05 : 0.01).concat([stepInput]),
          label: agent.rewards,
          sign,
        });
      }
    },

    determineWinner({ field, sign }) {
      return hasVictory.horizontalGroup({ field, sign })
        || hasVictory.verticalGroup({ field, sign, start: 0, step: 2 })
        || hasVictory.obliquelyGroup({ field, sign });
    },

    saveTraining({ input, label, sign }) {
      this.training[sign].inputs.push(input);
      this.training[sign].labels.push(label);

      this.trainingCount[sign] += 1;
    },

    async modelFit({ model, sign }) {
      if (this.trainingCount[sign] > 0) {
        this.trainingCount[sign] = 0;
        this.victoriesStatus[sign] = false;

        await model.fit(
          tf.tensor2d(this.training[sign].inputs),
          tf.tensor2d(this.training[sign].labels),
          { epochs: 1 },
        );

        this.training[sign].inputs = [];
        this.training[sign].labels = [];

        this.agentsSetting({ sign: 'X' });
        this.agentsSetting({ sign: 'O' });
      }
    },

    setSign(agent, cellIndex) {
      const { sign } = agent;

      if (!isAutomatic && agent.field[cellIndex].length === 0) {
        agent.field.splice(cellIndex, 1, sign);
        agent.rewards = agent.rewards.map((weight) => weight + 0.1);

        const isWinner = hasVictory.horizontalGroup({ field: agent.field, sign })
          || hasVictory.verticalGroup({ field: agent.field, sign, start: 0, step: 2 })
          || hasVictory.obliquelyGroup({ field: agent.field, sign });

        if (isWinner) {
          agent.isAlive = false;
          agent.isVictory = true;
        }

        console.log('isWinner', isWinner);
      }
    },

    setTimer() {
      setTimeout(this.setTimer, 1000);
      this.timer = Math.round((performance.now() - this.timerStart) / 1000);
    },

    // todo сброс накопленных данных: fields step rewards
    // todo количество ничьих.
    async setHumanSign(humanCellIndex) {
      const { field, step } = this.AIvsHuman;

      if (field[humanCellIndex].length === 0) {
        field.splice(humanCellIndex, 1, 'X');
        this.AIvsHuman.rewards = this.AIvsHuman.rewards.map((weight) => weight + 0.1);

        const isHumanWinner = this.determineWinner({ field, sign: 'X' });
        // todo если выиграл - остановка и сброс игры. счёткичи
        console.log('isHumanWinner', isHumanWinner);

        this.AIvsHuman.step += 1;
      } else {
        // todo конец игры. игрок проиграл
      }

      let stepInput;

      if (step <= 3) {
        stepInput = step / 3;
      } else {
        stepInput = 1 - (step / this.fieldSize);
      }

      const predictions = await this.modelO.predict(tf.tensor2d([this.AIvsHuman.rewards.concat([stepInput])])).data();
      const AICellIndex = predictions.indexOf(Math.max(...predictions));

      if (field[AICellIndex].length === 0) {
        field.splice(AICellIndex, 1, 'O');
        this.AIvsHuman.rewards = this.AIvsHuman.rewards.map((weight) => weight + 0.1);

        const isAIWinner = this.determineWinner({ field, sign: 'O' });
        console.log('isAIWinner', isAIWinner);
      } else {
        // todo конец игры. ai проиграл
      }
    },
  },
};
</script>

<style scoped>
.TicTacToe {
  --quantity-rows: 3;
  --quantity-columns: 3;
  --square-size: 64px;

  position: relative;
  margin-top: 150px;
  display: flex;
  justify-content: center;
  width: 100%;
  user-select: none;
}

.stat {
  position: absolute;
  top: 0;
  margin-top: -80px;
  width: 100%;
  text-align: center;
  color: white;
}

.stat .title {
  font-size: 16px;
  color: darkgray;
}

.stat .title span {
  font-weight: bold;
}

.stat .description {
  font-size: 14px;
  color: gray;
}

.stat .timer {
  font-size: 12px;
  color: dimgray;
}

.fields {
  position: relative;
  display: flex;
}

.field {
  margin: 5px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;
}

.field .cell {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 30px;
  color: #999;
  background-color: #444;
}

.field .cell.victory {
  background-color: darkgoldenrod;
}

.field .caption {
  position: absolute;
  bottom: -20px;
  width: 50%;
  text-align: center;
  font-size: 14px;
  color: dimgray;
}

.duel-field {
  position: relative;
  margin: 5px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;
}

.duel-field .cell {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 30px;
  font-weight: bold;
  color: white;
  background-color: #222;
}

.duel-field .cell.X {
  color: #c94c4c;
}

.duel-field .cell.O {
  color: #034f84;
}

.duel-field .cell.victory {
  background-color: gold;
}

.duel-field .caption {
  position: absolute;
  bottom: -25px;
  width: 100%;
  text-align: center;
  font-size: 14px;
  color: dimgray;
}

.fields-description {
  position: absolute;
  bottom: -90px;
  width: 100%;
  text-align: center;
  font-size: 14px;
  color: dimgray;
}

.ai-vs-human-container {
  position: absolute;
  top: 380px;
}

.ai-vs-human-container .caption {
  text-align: center;
  font-weight: bold;
  color: gray;
}

.ai-vs-human-container .field {
  margin-top: 10px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;
}

.ai-vs-human-container .field .cell {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 30px;
  color: white;
  background-color: #222;
}
</style>
