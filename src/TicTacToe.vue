<template>
  <div class="TicTacToe">
    <div class="stat">
      <div class="title">
        <span>Победы в соревнованиях:</span>

        <span class="X">
          X
        </span>

        <span class="victory">
          {{ victories.X }}
        </span>
        ˑ
        <span class="O">
          O
        </span>

        <span class="victory">
          {{ victories.O }}
        </span>
      </div>

      <div class="description">
        Количество тренировок и соревнований: {{ trainingGames + duelGames }}
      </div>

      <div class="timer">
        Время обучения: {{ timer }} секунд (~{{ Math.round(timer / 60) }} минут)
      </div>
    </div>

    <div class="fields-container">
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
          Поле для соревнований
        </div>
      </div>
    </div>

    <div class="fields-description">
      <div>9 игр - игроки на своих полях учатся играть, 1 игра - соревнование.</div>
      <br>
      <b>Начать игру с AI можно поставив знак на поле ниже - обучение приостановится.</b>
    </div>

    <div class="ai-vs-human-container">
      <div class="result">
        <span class="X">
          X
        </span>

        <span :class="[AIvsHuman.victories.X >= 0 ? 'success' : 'loss']">
          {{ AIvsHuman.victories.X }}
        </span>
        ˑ
        <span class="O">
          O
        </span>

        <span :class="[AIvsHuman.victories.O >= 0 ? 'success' : 'loss']">
          {{ AIvsHuman.victories.O }}
        </span>
      </div>

      <div class="caption">
        Человек против AI
      </div>

      <div class="field">
        <div
          v-for="(sign, cellIndex) in AIvsHuman.field"
          :key="cellIndex"
          :class="['cell', sign, { victory: victoriesStatus[sign] }]"
          @click="setHumanSign(cellIndex)"
        >
          {{ sign }}
        </div>
      </div>

      <button
        :class="['resume', 'button', { 'is-duel': AIvsHuman.isDuel }]"
        @click="AIvsHumanReset"
      >
        Продолжить обучение
      </button>

      <div class="models-controller">
        <div class="button-container">
          <button
            class="button"
            @click="saveModelsOnPC"
          >
            Сохранить модели на компьютер
          </button>
        </div>

        <div class="button-container">
          <button
            class="button"
            @click="localStorageClear"
          >
            Очистить локальное хранилище
          </button>
        </div>

        <div class="button-container">
          <button
            class="button"
            @click="restoreModelsFromGitHub"
          >
            Ввести модели из GitHub
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import { victoryCheckGroups as hasVictory } from './utils';

const isAutomatic = true;
const isDuel = true;
const isDelay = false;

const worstReward = -1.0;
const lossReward = -0.4;
const basicReward = 0.1;
const stepReward = 0.2;
const interestReward = 0.5;
const bestReward = 1.0;

const mountedIndex = 11;

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

      timer: 0,
      timeTraining: 5 * 60,

      isDuel: false,
      duel: {
        step: 1,
        field: [
          '', '', '',
          '', '', '',
          '', '', '',
        ],
      },
      duelGames: 1,

      AIvsHuman: {
        isDuel: false,
        step: 1,
        victories: { X: 0, O: 0 },
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
    console.log(mountedIndex);

    const timer = JSON.parse(localStorage.getItem('syntet_TicTacToe_timer'));

    if (timer) {
      this.timer = timer;
      this.restoreFromLocalStorage();

      const [modelX, modelO] = await Promise.all([
        tf.loadLayersModel('localstorage://syntet_TicTacToe_model_X'),
        tf.loadLayersModel('localstorage://syntet_TicTacToe_model_O'),
      ]);

      localStorage.clear();

      modelX.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });

      modelO.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });

      this.modelX = modelX;
      this.modelO = modelO;
    } else {
      this.setupModel({ model: this.modelX });
      this.setupModel({ model: this.modelO });
    }

    this.agentsSetting({ sign: 'X' });
    this.agentsSetting({ sign: 'O' });

    this.setTimer();

    if (isAutomatic) {
      this.gameLoop();
    }
  },

  methods: {
    restoreFromLocalStorage() {
      this.trainingCount = JSON.parse(localStorage.getItem('syntet_TicTacToe_trainingCount'));
      this.victories = JSON.parse(localStorage.getItem('syntet_TicTacToe_victories'));
      this.trainingGames = JSON.parse(localStorage.getItem('syntet_TicTacToe_trainingGames'));
      this.duelGames = JSON.parse(localStorage.getItem('syntet_TicTacToe_duelGames'));
      this.AIvsHuman.victories = JSON.parse(localStorage.getItem('syntet_TicTacToe_AIvsHuman_victories'));
    },

    setupModel({ model }) {
      model.add(tf.layers.dense({
        // +1 - Количество ходов.
        inputShape: [this.fieldSize + 1],
        activation: 'sigmoid',
        units: 128,
      }));

      // model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 32,
      // }));

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

    setTimer() {
      setTimeout(this.setTimer, 1000);
      this.timer += 1;
    },

    async gameLoop() {
      if (this.AIvsHuman.isDuel) {
        this.agentsSetting({ sign: 'X' });
        this.agentsSetting({ sign: 'O' });

        await new Promise((resolve) => setTimeout(resolve, 300));
        this.gameLoop();
        return;
      }

      if (this.isDuel && isDuel) {
        await this.startDuel();
        this.duelGames += 1;
      } else {
        this.isDuel = this.trainingGames % this.fieldSize === 0;

        await this.startTraining();
        this.trainingGames += 1;
      }

      if (isDelay) {
        await new Promise((resolve) => setTimeout(resolve, 300));
      }

      if (this.timer !== 0 && this.timer % this.timeTraining === 0) {
        this.saveInLocalStorage();
        await this.saveModelsLocal();

        // Высвобождение ресурсов, чтобы не зависала вкладка.
        window.location.reload();
      }

      this.gameLoop();
    },

    saveInLocalStorage() {
      localStorage.setItem('syntet_TicTacToe_timer', JSON.stringify(this.timer));
      localStorage.setItem('syntet_TicTacToe_trainingCount', JSON.stringify(this.trainingCount));
      localStorage.setItem('syntet_TicTacToe_victories', JSON.stringify(this.victories));
      localStorage.setItem('syntet_TicTacToe_trainingGames', JSON.stringify(this.trainingGames));
      localStorage.setItem('syntet_TicTacToe_duelGames', JSON.stringify(this.duelGames));
      localStorage.setItem('syntet_TicTacToe_AIvsHuman_victories', JSON.stringify(this.AIvsHuman.victories));
    },

    async saveModelsLocal() {
      await this.modelX.save('localstorage://syntet_TicTacToe_model_X');
      await this.modelO.save('localstorage://syntet_TicTacToe_model_O');
    },

    async startDuel() {
      let taskCount = 2;

      await new Promise((resolve) => {
        const agents = this.agents.X.filter(({ isAlive }) => isAlive);
        let count = agents.length;

        if (count > 0) {
          agents.forEach(async (agent) => {
            await this.modelPredict({ model: this.modelX, agent });
            count -= 1;

            if (count === 0) {
              resolve();
            }
          });
        } else {
          taskCount -= 1;
          resolve();
        }
      });

      await new Promise((resolve) => {
        const agents = this.agents.O.filter(({ isAlive }) => isAlive);
        let count = agents.length;

        if (count > 0) {
          agents.forEach(async (agent) => {
            await this.modelPredict({ model: this.modelO, agent });
            count -= 1;

            if (count === 0) {
              resolve();
            }
          });
        } else {
          taskCount -= 1;
          resolve();
        }
      });

      if (taskCount === 2) {
        this.duel.step = this.fieldSize;
      }

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

    // Знаки обучаются ходить.
    async startTraining() {
      const tasks = this.agents.X.filter(({ isAlive }) => isAlive)
        .map((agent) => this.modelPredict({ model: this.modelX, agent }))
        .concat(this.agents.O.filter(({ isAlive }) => isAlive)
          .map((agent) => this.modelPredict({ model: this.modelO, agent })));

      if (tasks.length === 0) {
        this.step = this.fieldSize;
      } else {
        await Promise.all(tasks);
      }

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

    async modelPredict({ model, agent }) {
      const step = this.isDuel ? this.duel.step : this.step;
      const field = this.isDuel ? this.duel.field : agent.field;

      this.increasingInterest({ field, agent });

      const stepInput = this.getStepInput(step);
      const predictions = await model.predict(tf.tensor2d([agent.rewards.concat([stepInput])])).data();
      const cellIndex = predictions.indexOf(Math.max(...predictions));

      if (field[cellIndex].length === 0) {
        const { sign } = agent;
        field.splice(cellIndex, 1, sign);

        agent.rewards = this.recalculateRewards({ rewards: agent.rewards, field });
        const isWinner = this.determineWinner({ field, sign });

        if (isWinner) {
          agent.isAlive = false;
          agent.isVictory = true;
          agent.rewards[cellIndex] = bestReward;

          this.saveTraining({ type: 'winner', field, agent, stepInput });

          if (this.isDuel) {
            this.victories[sign] += 1;
            this.victoriesStatus[sign] = true;
          }
        } else {
          agent.rewards[cellIndex] = basicReward;
          this.saveTraining({ type: 'step', field, agent, stepInput });
        }
      } else {
        agent.isAlive = false;
        agent.rewards = this.recalculateRewards({ rewards: agent.rewards, field });

        this.saveTraining({ type: 'loss', field, agent, stepInput });
      }
    },

    // Повышение интереса для хода к потенциально выигрышной ячейки противника.
    increasingInterest({ field, agent }) {
      const signNextTurn = agent.sign === 'X' ? 'O' : 'X';

      for (let i = 0; i < field.length; i += 1) {
        if (field[i].length === 0) {
          field.splice(i, 1, agent.sign);
          const isWinner = this.determineWinner({ field, sign: agent.sign });
          field.splice(i, 1, '');

          if (isWinner) {
            agent.rewards[i] = bestReward;
            break;
          }

          // ---

          field.splice(i, 1, signNextTurn);
          const isOtherWinner = this.determineWinner({ field, sign: signNextTurn });
          field.splice(i, 1, '');

          if (isOtherWinner) {
            agent.rewards[i] = interestReward;
            break;
          }
        }
      }
    },

    getStepInput(step) {
      return 1 - (step / this.fieldSize);
    },

    recalculateRewards({ rewards, field }) {
      return rewards.map((_, index) => {
        let reward;

        if (field[index].length === 0) {
          reward = basicReward;
        } else {
          reward = worstReward;
        }

        return reward;
      });
    },

    determineWinner({ field, sign }) {
      return hasVictory.horizontalGroup({ field, sign })
        || hasVictory.verticalGroup({ field, sign, start: 0, step: 2 })
        || hasVictory.obliquelyGroup({ field, sign });
    },

    saveTraining({ type, field, agent, stepInput }) {
      const { sign, rewards: label } = agent;
      const input = field.map((cell) => this.trafficLights({ type, sign, cell })).concat([stepInput]);

      this.training[sign].inputs.push(input);
      this.training[sign].labels.push(label);

      this.trainingCount[sign] += 1;
    },

    trafficLights({ type, sign, cell }) {
      let reward = basicReward;

      // Если ячейка свободна, то это нормально, но если занято другим знаком - это плохо.
      if (type === 'winner') {
        if (sign === cell) {
          reward = bestReward;
        } else if (cell.length === 0) {
          reward = basicReward;
        } else {
          reward = worstReward;
        }
      } else if (type === 'step') {
        if (sign === cell) {
          reward = stepReward;
        } else if (cell.length === 0) {
          reward = basicReward;
        } else {
          reward = worstReward;
        }
      } else if (type === 'loss') {
        if (sign === cell) {
          reward = lossReward;
        } else if (cell.length === 0) {
          reward = basicReward;
        } else {
          reward = worstReward;
        }
      }

      return reward;
    },

    async modelFit({ model, sign }) {
      if (this.trainingCount[sign] > 0) {
        // Где то данные не кладутся, но счётчик увеличивается.
        if (this.training[sign].inputs.length === 0 || this.training[sign].labels.length === 0) {
          return;
        }

        this.trainingCount[sign] = 0;
        this.victoriesStatus[sign] = false;

        await model.fit(
          tf.tensor2d(this.training[sign].inputs),
          tf.tensor2d(this.training[sign].labels),
        );

        this.trainingReset(sign);

        this.agentsSetting({ sign: 'X' });
        this.agentsSetting({ sign: 'O' });
      }
    },

    trainingReset(sign) {
      this.training[sign].inputs = [];
      this.training[sign].labels = [];
    },

    async setHumanSign(humanCellIndex) {
      if (!this.AIvsHuman.isDuel) {
        this.AIvsHuman.isDuel = true;

        this.trainingReset('X');
        this.trainingReset('O');
      }

      const { isPass } = await this.humanSignXO({ sign: 'X', cIndex: humanCellIndex });

      if (isPass) {
        await this.humanSignXO({ sign: 'O', cIndex: -1 });
      }
    },

    async humanSignXO({ sign, cIndex }) {
      if (this.AIvsHuman.step > this.fieldSize) {
        this.AIvsHumanReset();
        return { isPass: false };
      }

      this.AIvsHuman.step += 1;
      const stepInput = this.getStepInput(this.AIvsHuman.step);

      const { field } = this.AIvsHuman;
      let cellIndex = cIndex;

      if (sign === 'O') {
        this.increasingInterest({ field, agent: this.AIvsHuman });

        const predictions = await this.modelO.predict(tf.tensor2d([this.AIvsHuman.rewards.concat([stepInput])])).data();
        cellIndex = predictions.indexOf(Math.max(...predictions));
      }

      if (field[cellIndex].length === 0) {
        field.splice(cellIndex, 1, sign);

        this.AIvsHuman.rewards = this.recalculateRewards({ rewards: this.AIvsHuman.rewards, field });
        const isWinnerXO = this.determineWinner({ field, sign });

        if (isWinnerXO) {
          const agent = { sign, rewards: this.AIvsHuman.rewards };
          this.saveTraining({ type: 'winner', field, agent, stepInput });

          this.AIvsHuman.victories[sign] += 1;
          await this.AIvsHumanFit();

          return { isPass: false };
        }

        // Даст выход -> return { isPass: true };
      } else {
        this.AIvsHuman.rewards = this.recalculateRewards({ rewards: this.AIvsHuman.rewards, field });
        const agent = { sign, rewards: this.AIvsHuman.rewards };
        this.saveTraining({ type: 'loss', field, agent, stepInput });

        this.AIvsHuman.victories[sign] -= 1;
        await this.AIvsHumanFit();

        return { isPass: false };
      }

      return { isPass: true };
    },

    async AIvsHumanFit() {
      await Promise.all([
        this.modelFit({ model: this.modelX, sign: 'X' }),
        this.modelFit({ model: this.modelO, sign: 'O' }),
      ]);

      this.AIvsHumanReset();
    },

    AIvsHumanReset() {
      this.AIvsHuman = {
        ...this.AIvsHuman,
        isDuel: false,
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
      };
    },

    async saveModelsOnPC() {
      try {
        await Promise.all([
          this.modelX.save('downloads://syntet_TicTacToe_model_X'),
          this.modelO.save('downloads://syntet_TicTacToe_model_O'),
        ]);
      } catch (err) {
        console.error('saveModels', err);
      }
    },

    localStorageClear() {
      localStorage.clear();
    },

    async restoreModelsFromGitHub() {
      const uriModelX = './models/syntet_TicTacToe_model_X.json';
      const uriModelO = './models/syntet_TicTacToe_model_O.json';

      const [modelX, modelO] = await Promise.all([
        tf.loadLayersModel(uriModelX),
        tf.loadLayersModel(uriModelO),
      ]);

      modelX.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });

      modelO.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });

      this.modelX = modelX;
      this.modelO = modelO;
    },
  },
};
</script>

<style
  lang="scss"
  scoped
>
.TicTacToe {
  --quantity-rows: 3;
  --quantity-columns: 3;
  --square-size: 64px;

  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100vh;
  user-select: none;
}

.stat {
  text-align: center;
  color: white;

  .title {
    font-size: 16px;
    font-weight: bold;
    color: darkgray;

    .X {
      color: #c94c4c;
    }

    .O {
      color: #034f84;
    }

    .victory {
    }
  }

  .description {
    font-size: 14px;
    color: gray;
  }

  .timer {
    font-size: 12px;
    color: dimgray;
  }
}

.fields-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.fields {
  position: relative;
  display: flex;

  .field {
    margin: 5px;
    display: grid;
    grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
    grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
    grid-gap: 1px;

    .cell {
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 30px;
      color: #999;
      background-color: #444;

      &.victory {
        background-color: darkgoldenrod;
      }
    }

    .caption {
      position: absolute;
      bottom: -20px;
      width: 50%;
      text-align: center;
      font-size: 14px;
      color: dimgray;
    }
  }
}

.duel-field {
  position: relative;
  margin: 5px;
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
  grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
  grid-gap: 1px;

  .cell {
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 30px;
    font-weight: bold;
    color: white;
    background-color: #222;

    &.X {
      color: #c94c4c;
    }

    &.O {
      color: #034f84;
    }

    &.victory {
      background-color: gold;
    }
  }

  .caption {
    position: absolute;
    bottom: -25px;
    width: 100%;
    text-align: center;
    font-size: 14px;
    color: dimgray;
  }
}

.fields-description {
  margin-top: 45px;
  text-align: center;
  line-height: 1;
  font-size: 14px;
  color: dimgray;
}

.ai-vs-human-container {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;

  .result {
    margin-top: 5px;
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    color: gray;

    .X {
      color: #c94c4c;
    }

    .O {
      color: #034f84;
    }

    .success {
      color: green;
    }

    .loss {
      color: red;
    }
  }

  .caption {
    text-align: center;
    font-size: 14px;
    font-weight: bold;
    color: gray;
  }

  .field {
    margin-top: 10px;
    display: grid;
    grid-template-rows: repeat(var(--quantity-rows), var(--square-size));
    grid-template-columns: repeat(var(--quantity-columns), var(--square-size));
    grid-gap: 1px;

    .cell {
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 30px;
      font-weight: bold;
      color: white;
      background-color: #222;

      &.X {
        color: #c94c4c;
      }

      &.O {
        color: #034f84;
      }
    }
  }

  .resume {
    margin-top: 10px;
    color: #333;

    &.is-duel {
      color: white;
    }
  }

  .models-controller {
    margin-top: 10px;
    text-align: center;

    .button-container {
      margin-top: 5px;
    }
  }
}

.button {
  padding: 4px 6px;
  border: none;
  text-align: center;
  color: darkgrey;
  background-color: #222;
  outline: none;
}
</style>
