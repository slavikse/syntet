<template>
  <div>
    <div class="stat time">
      Секунд прошло: {{ startTime }}
    </div>

    <div class="stat epoch">
      Шаг: {{ actor.step }} | Эпох: {{ epoch }} | Побед: {{ win }}
    </div>

    <div
      ref="Square"
      class="Square"
      tabindex="0"
      @keyup.up="handJumpTop"
      @keyup.right="handJumpRight"
      @keyup.down="handJumpBottom"
      @keyup.left="handJumpLeft"
    >
      <div class="cells field">
        <div
          v-for="(cellValue, index) in field"
          :key="index"
          :data-cell-value="cellValue"
          :class="['cell', { 'available': cellValue !== 0 }]"
        >
          <div
            v-if="cellValue === 1"
            class="starting-checkpoint"
          >
            СТАРТ
          </div>

          <div
            v-if="cellValue === 45"
            class="finishing-checkpoint"
          >
            ФИНИШ
          </div>
        </div>
      </div>

      <div class="players field">
        <div class="player">
          <div class="actor">
            🐥
          </div>

          <!-- Усики сканирующие, что там дальше. -->
          <div class="antenna jump-top" />
          <div class="antenna jump-right" />
          <div class="antenna jump-bottom" />
          <div class="antenna jump-left" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';

const automaticControl = true;

const maxCellValues = 45;
// Минимальное количество ходов для выигрыша.
const maxStep = maxCellValues * 5;

// Обязательно квадратной формы, для Math.sqrt(this.field.length).
// @formatter:off
/* eslint-disable no-multi-spaces */
// Обязательно между доступным путём, должно быть 2 запретных ячейки из за усиков.
const field = [
  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
  0,  1,  0,  0,  0,  0,  0,  0,  0, 45, 44, 43,  0,
  0,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0, 42,  0,
  0,  3,  0,  0,  8,  9, 10, 11,  0,  0,  0, 41,  0,
  0,  4,  5,  6,  7,  0,  0, 12,  0,  0,  0, 40,  0,
  0,  0,  0,  0,  0,  0,  0, 13,  0,  0,  0, 39,  0,
  0,  0,  0,  0,  0,  0, 15, 14,  0,  0,  0, 38,  0,
  0,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0, 37,  0,
  0,  0, 21, 20, 19, 18, 17,  0,  0,  0,  0, 36,  0,
  0,  0, 22,  0,  0,  0,  0,  0,  0, 33, 34, 35,  0,
  0,  0, 23,  0,  0,  0,  0,  0,  0, 32,  0,  0,  0,
  0,  0, 24, 25, 26, 27, 28, 29, 30, 31,  0,  0,  0,
  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
];
/* eslint-enable no-multi-spaces */
// @formatter:on

export default {
  name: 'Square',

  data() {
    return {
      time: Date(),
      startTime: 0,
      style: undefined,

      // Игровая область обязательно квадратной формы.
      // 0 - Запретная территория.
      // 1 - Проходная территория.
      // 2 - Начальная точка.
      // 3 - Промежуточная точка.
      // 4 - Финишная точка.
      field,
      size: -1,
      quantityColumns: -1,
      quantityRows: -1,

      actor: {
        x: 2,
        y: 2,
        step: 0,
      },

      model: tf.sequential(),
      epoch: 0,
      win: 0,
      training: {
        // x, y - Нормализованные координаты актёра.
        // step - Количество шагов, сделанных от стартовой позиции.
        inputs: [],
        // [1, 0, 0, 0] - Пойти на север (north).
        // [0, 1, 0, 0] - Пойти на восток (east).
        // [0, 0, 1, 0] - Пойти на юг (south).
        // [0, 0, 0, 1] - Пойти на запад (west).
        labels: [],
      },
    };
  },

  async mounted() {
    this.setupModel();

    // Timer.
    setInterval(() => {
      this.time = Date();
      this.startTime += 1;
    }, 1000);

    this.style = this.$refs.Square.style;

    this.settingPlayingField();
    await this.setPlayerStyleProperties();

    if (automaticControl) {
      await this.modelPredict();
    }
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        // Описание в training.inputs.
        inputShape: [3],
        activation: 'sigmoid',
        units: 256,
      }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: 256,
      }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        // [north, east, south, west] - Прогноз стороны для передвижения.
        units: 4,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.01),
        loss: 'meanSquaredError',
      });
    },

    settingPlayingField() {
      this.size = Math.sqrt(this.field.length);
      this.quantityColumns = this.size;
      this.quantityRows = this.size;

      this.style.setProperty('--quantity-columns', this.quantityColumns);
      this.style.setProperty('--quantity-rows', this.quantityRows);
    },

    async setPlayerStyleProperties() {
      const { x, y } = this.actor;

      this.style.setProperty('--player-column', x);
      this.style.setProperty('--player-row', y);

      if (this.actor.step === maxStep) {
        await this.modelFit();
      }
    },

    async modelPredict() {
      const {
        x,
        y,
        step,
      } = this.actor;

      const prediction = this.model.predict(tf.tensor2d([
        [
          x / this.size,
          y / this.size,
          step / maxStep,
        ],
      ]));

      const [jumpTop, jumpRight, jumpBottom, jumpLeft] = await prediction.data();

      console.log(
        'Top', jumpTop.toFixed(4),
        'Right', jumpRight.toFixed(4),
        'Bottom', jumpBottom.toFixed(4),
        'Left', jumpLeft.toFixed(4),
      );

      let maximum = jumpTop;
      let action = 'jumpTop';

      if (jumpRight > maximum) {
        maximum = jumpRight;
        action = 'jumpRight';
      }

      if (jumpBottom > maximum) {
        maximum = jumpBottom;
        action = 'jumpBottom';
      }

      if (jumpLeft > maximum) {
        maximum = jumpLeft;
        action = 'jumpLeft';
      }

      this[action]();

      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    jumpTop() {
      this.actor.y -= 1;
    },

    jumpRight() {
      this.actor.x += 1;
    },

    jumpBottom() {
      this.actor.y += 1;
    },

    jumpLeft() {
      this.actor.x -= 1;
    },

    async checkExit() {
      const { x, y } = this.actor;
      // Смещение на -1: Сетка начинается с 1, а значения в массиве начинаются с 0.
      const normalY = y - 1;
      const normalX = x - 1;
      const cellValue = this.field[normalY * this.size + normalX];

      // Очень важно передавать значения в label[] в таком же порядке!
      const [top, right, bottom, left] = this.getAntennaCellValues({ normalX, normalY });

      const label = [
        top / maxCellValues,
        right / maxCellValues,
        bottom / maxCellValues,
        left / maxCellValues,
      ];

      // Тренировать на накопленных training.inputs при выходе за границы.
      let isModelFit = false;
      // Сброс для успешного прохождения.
      let isReset = false;

      if (cellValue === 0) {
        isModelFit = true;
      } else if (cellValue > 0 && cellValue < maxCellValues) {
        this.actor.step += 1;
      } else if (cellValue === maxCellValues) {
        isReset = true;
        console.log('ФИНИШ!', x, y);

        this.actor.step += 1;
        this.win += 1;
      }

      // if (!automaticControl) {
      //   // Для проверки, куда актёр пришёл.
      //   console.log(`x: ${x}, y: ${y}, step: ${this.actor.step}, cellValue: ${cellValue}, label: ${label}`);
      //   console.log(`top: ${top}, right: ${right}, bottom: ${bottom}, left: ${left}`);
      // }

      this.training.inputs.push([
        x / this.size,
        y / this.size,
        this.actor.step / maxStep,
      ]);

      this.training.labels.push(label);

      if (isModelFit) {
        await this.modelFit();
      }

      if (isReset) {
        await this.resetGame();
      }

      if (automaticControl) {
        await this.modelPredict();
      }
    },

    // Получение значения ячейки от 1 до 4.
    getAntennaCellValues({ normalX, normalY }) {
      // || 0 - когда выходит на запретную зону, то дальше нет пути, считаем, что тоже запретная.
      const top = this.field[(normalY - 1) * this.size + normalX] || 0;
      const right = this.field[normalY * this.size + (normalX + 1)] || 0;
      const bottom = this.field[(normalY + 1) * this.size + normalX] || 0;
      const left = this.field[normalY * this.size + (normalX - 1)] || 0;

      return [top, right, bottom, left];
    },

    async modelFit() {
      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );

      this.epoch += 1;
      await this.resetGame();
    },

    async resetGame() {
      this.actor = {
        ...this.actor,
        x: 2,
        y: 2,
        step: 0,
      };

      await this.setPlayerStyleProperties();
    },

    // Специально для ручного управления.
    async handJumpTop() {
      this.jumpTop();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    async handJumpRight() {
      this.jumpRight();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    async handJumpBottom() {
      this.jumpBottom();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },

    async handJumpLeft() {
      this.jumpLeft();
      await this.setPlayerStyleProperties();
      this.checkExit();
    },
  },
};
</script>

<style
  lang='scss'
  scoped
>
.Square {
  --quantity-rows: -1;
  --quantity-columns: -1;
  --column-width: 3rem;

  --player-row: -1;
  --player-column: -1;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;
  user-select: none;
}

.stat {
  position: absolute;
  z-index: 1;
  font-size: 1.2rem;
  color: white;
}

.time {
  margin-top: 3rem;
  width: 100%;
  text-align: center;
}

.epoch {
  margin-top: 5rem;
  width: 100%;
  text-align: center;
}

.cells {
  .cell {
    position: relative;
    display: flex;
    background-color: #222;
  }

  .available {
    background-color: darkcyan;
  }

  .starting-checkpoint,
  .middle-checkpoint,
  .finishing-checkpoint {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100%;
    line-height: 0.9;
    font-size: 0.7rem;
    font-weight: bold;
    background-color: seagreen;
    outline: 0.5rem dashed seagreen;
  }

  .middle-checkpoint {
    line-height: 1;
    color: green;
    background-color: greenyellow;
    outline: 0.2rem dashed greenyellow;
  }
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--column-width));
  grid-template-columns: repeat(var(--quantity-columns), var(--column-width));
  grid-gap: 0.5rem;
}

.players {
  position: absolute;

  .player {
    position: relative;
    grid-row: var(--player-row);
    grid-column: var(--player-column);
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: yellow;
    outline: 0.5rem dashed yellow;

    .actor {
      font-size: 2.4rem;
    }

    .antenna {
      position: absolute;
      height: 2px;
      width: 1.5rem;
      background-color: brown;
    }

    .jump-top {
      top: -1.3rem;
      transform: rotate(90deg);
    }

    .jump-right {
      right: -2rem;
      transform: rotate(180deg);
    }

    .jump-bottom {
      bottom: -1.3rem;
      transform: rotate(270deg);
    }

    .jump-left {
      left: -2rem;
    }
  }
}
</style>
