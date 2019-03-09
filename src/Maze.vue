<template>
  <a-scene
    id="Maze"
    physics="debug: false"
    stats="false"
    vr-mode-ui="enabled: false"
  >
    <div class="stat time">
      {{ time }} / Прошло секунд: {{ startTime }}.
    </div>

    <div class="stat epoch">
      Эпоха: {{ epoch }}
    </div>

    <a-assets id="AssetsImages">
      <img
        id="AssetsImagesFloor"
        src="./assets/images/floor.jpg"
      >

      <img
        id="AssetsImagesWall"
        src="./assets/images/wall.jpg"
      >

      <img
        id="AssetsImagesRoof"
        src="./assets/images/roof.jpg"
      >
    </a-assets>

    <!-- LightsAmbient -->
    <a-light
      id="LightsAmbient"
      type="ambient"
      intensity="5"
    />

    <!-- WallsFloor -->
    <a-plane
      id="WallsFloor"
      src="#AssetsImagesFloor"
      position="12.5 -2 12.5"
      rotation="-90 0 0"
      height="80"
      width="80"
      repeat="20 30"
      material="color: #333"
      static-body
    />

    <!-- Triggers -->
    <a-box
      v-for="({ name, position }, index) in triggers"
      :id="`Triggers_${name}_${index}`"
      :key="`Triggers_${name}_${index}`"
      :position="position"
      src="#AssetsImagesRoof"
      height="0.1"
      width="2"
      depth="2"
      material="color: #111"
      static-body
    />

    <!-- Fences -->
    <a-box
      v-for="({ name, position, rotation }, index) in fences"
      :id="`Fences_${name}_${index}`"
      :key="`Fences_${name}_${index}`"
      :position="position"
      :rotation="rotation"
      src="#AssetsImagesWall"
      height="1"
      width="30"
      repeat="5 1"
      material="color: #444"
      static-body
      class="collidable"
    />

    <!-- Walls -->
    <a-box
      v-for="({ name, position, rotation }, index) in walls"
      :id="`Walls_${name}_${index}`"
      :key="`Walls_${name}_${index}`"
      :position="position"
      :rotation="rotation"
      src="#AssetsImagesWall"
      height="1"
      width="5"
      material="color: #444"
      static-body
      class="collidable"
    />

    <!--
    <a-box
      v-for="({ name, position, rotation }, index) in traveled"
      :id="`Traveleds_${name}_${index}`"
      :key="`Traveleds_${name}_${index}`"
      :position="position"
      :rotation="rotation"
      src="#AssetsImagesWall"
      height="2"
      width="2"
      material="color: #444"
      static-body
      class="collidable"
    />
    -->

    <!-- Actor -->
    <a-box
      id="Actor"
      src="#AssetsImagesRoof"
      :animation="{
        property: 'position',
        easing: 'linear',
        to: actor.position,
        dur: actor.delay,
      }"
      kinematic-body
      height="0.1"
      width="1.5"
      depth="1.5"
      material="color: #257"
    >
      <a-entity
        v-for="({ name, rotation }, index) in raycasters"
        :key="index"
        :rotation="rotation"
        raycaster="
          objects: .collidable;
          showLine: true;
          far: 1.5;
        "
        @raycaster-intersection="intersected(name)"
      />
    </a-box>

    <a-entity
      id="Spectator"
      :position="spectator.position"
      rotation="-90 0 0"
      movement-controls="speed: 2"
    >
      <a-entity
        id="SpectatorCamera"
        camera
        look-controls
      />
    </a-entity>
  </a-scene>
</template>

<script>
import * as tf from '@tensorflow/tfjs';

// Размер шага актёра для x (x), y (z).
const step = 2.5;
const maxStep = 10;

// Размер максимального количества шагов для сторон X и Y начиная с 0.
const maxStepX = step * maxStep;
const maxStepY = step * maxStep;

// Порог прохождения (вероятность) для принятия решения.
const threshold = 0.4;
let modelPredictId;

export default {
  name: 'Maze',

  data() {
    return {
      triggers: [
        {
          name: 'Start',
          position: '0 0 0',
        },
        {
          // todo 0 0 25
          name: 'Between_1',
          position: '0 0 20',
        },
        {
          name: 'Finish',
          position: '25 0 25',
        },
      ],
      fences: [
        {
          name: 'Top',
          position: '12.5 0 -2.5',
          rotation: '0 0 0',
        },
        {
          name: 'Right',
          position: '27.5 0 12.5',
          rotation: '0 90 0',
        },
        {
          name: 'Bottom',
          position: '12.5 0 27.5',
          rotation: '0 180 0',
        },
        {
          name: 'Left',
          position: '-2.5 0 12.5',
          rotation: '0 90 0',
        },
      ],
      walls: [
        {
          name: '1',
          position: '2.5 0 0',
          rotation: '0 -90 0',
        },
        {
          name: '2',
          position: '2.5 0 5',
          rotation: '0 -90 0',
        },
        {
          name: '3',
          position: '2.5 0 10',
          rotation: '0 -90 0',
        },
        {
          name: '4',
          position: '2.5 0 15',
          rotation: '0 -90 0',
        },
        {
          name: '5',
          position: '2.5 0 20',
          rotation: '0 -90 0',
        },
      ],

      spectator: {
        position: '12.5 20 12.5',
      },

      actor: {
        position: {
          x: 0,
          y: 0.2,
          z: 0,
        },
        delay: 1000,
      },
      // Хранится последние 3 хода, для исправления:
      // 1. Зацикливается на 2х шагах, которые не вредят.
      // 2. Стоит в 1 точке и ничего не делает.
      savedMoves: [],

      model: tf.sequential(),
      training: {
        // [x, y] - Нормализованные координаты актёра.
        inputs: [],
        // [1, 0, 0, 0] - Пойти на север (north).
        // [0, 1, 0, 0] - Пойти на восток (east).
        // [0, 0, 1, 0] - Пойти на юг (south).
        // [0, 0, 0, 1] - Пойти на запад (west).
        labels: [],
      },

      // Начальные координаты актёра в двухмерном пространстве.
      x: 0,
      y: 0,

      raycasters: [
        {
          name: 'north',
          rotation: '0 0 0',
        },
        {
          name: 'east',
          rotation: '0 90 0',
        },
        {
          name: 'south',
          rotation: '0 180 0',
        },
        {
          name: 'west',
          rotation: '0 270 0',
        },
      ],

      epoch: 0,
      time: Date(),
      startTime: 0,
    };
  },

  mounted() {
    // Timer.
    setInterval(() => {
      this.time = Date();
      this.startTime += 1;
    }, 1000);

    this.setupModel();
    modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
  },

  methods: {
    setupModel() {
      this.model.add(tf.layers.dense({
        inputShape: [2], // [x, y] - Нормализованные координаты актёра.
        activation: 'sigmoid',
        units: 16,
      }));

      this.model.add(tf.layers.dense({
        inputShape: [16],
        activation: 'sigmoid',
        units: 4, // [north, east, south, west] - Прогноз стороны для передвижения.
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.05),
        loss: 'meanSquaredError',
      });
    },

    // Прогноз сети для следующего действия.
    // todo зацикливается на 2х ячейках (запретить возвращаться на пройденную ячейку).
    // todo вообще останавливается.
    async modelPredict() {
      clearTimeout(modelPredictId);

      const prediction = this.model.predict(tf.tensor2d([
        [
          this.x / maxStepX,
          this.y / maxStepY,
        ],
      ]));

      const [north, east, south, west] = await prediction.data();
      console.log('north, east, south, west', north, east, south, west);

      let maximum = north;
      let action = 'north';

      if (east > maximum) {
        maximum = east;
        action = 'east';
      }

      if (south > maximum) {
        maximum = south;
        action = 'south';
      }

      if (west > maximum) {
        maximum = west;
        action = 'west';
      }

      if (maximum > threshold) {
        this[action]();
      }

      modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
    },

    north() {
      this.y -= step;
      this.actor.position.z = this.y;
    },

    east() {
      this.x += step;
      this.actor.position.x = this.x;
    },

    south() {
      this.y += step;
      this.actor.position.z = this.y;
    },

    west() {
      this.x -= step;
      this.actor.position.x = this.x;
    },

    // Обучит, что сейчас не время идти по этому направлению.
    // todo рассчётов очень много и актёр просто пролетает признаковую платформу поворота.
    async intersected(name) {
      clearTimeout(modelPredictId);

      let label = [0, 0, 0, 0];

      switch (name) {
        case 'north':
          label = [0, 0.5, 0.5, 0.5];
          break;

        case 'east':
          label = [0.5, 0, 0.5, 0.5];
          break;

        case 'south':
          label = [0.5, 0.5, 0, 0.5];
          break;

        case 'west':
          label = [0.5, 0.5, 0.5, 0];
          break;

        default:
          console.log('Упс!');
      }

      // console.log(`intersected ${name} / ${label}`);

      await this.modelFit({ label });
      modelPredictId = setTimeout(this.modelPredict, this.actor.delay);
    },

    async modelFit({ label }) {
      // При выигрыши нейросети - не нужно считать новую эпоху.
      let isContinue = true;

      // todo
      let isNext = false;

      if (this.x === 0 && this.y === maxStepY + step) {
        console.log('Between_1 !');
        isNext = true;
        // todo хитрость... что то тут хитрое нужно давать. предыдущий ход.
        label = [0, 0.7, 0, 0];
      } else if (this.x === maxStepX + step && this.y === maxStepY + step) {
        console.log('ФИНИШ!');
        // todo что то тут хитрое нужно давать. предыдущий ход.
        label = [0, 1, 0, 0];
        isContinue = false;
      }

      this.training.inputs.push([
        this.x / maxStepX,
        this.y / maxStepY,
      ]);

      console.log('X', this.x / maxStepX);
      console.log('Y', this.y / maxStepY);

      this.training.labels.push(label);

      await this.model.fit(
        tf.tensor2d(this.training.inputs),
        tf.tensor2d(this.training.labels),
      );

      if (!isNext) {
        this.resetGame({ isContinue });
      }
    },

    resetGame({ isContinue }) {
      if (isContinue) {
        this.epoch += 1;
      }

      this.x = 0;
      this.y = 0;

      this.actor.position.x = this.x;
      this.actor.position.z = this.y;
    },
  },
};
</script>

<style scoped>
.stat {
  position: absolute;
  z-index: 1;
  font-size: 1.2rem;
  color: white;
}

.time {
  left: 0.5rem;
}

.epoch {
  right: 0.5rem;
  font-size: 1.4rem;
}
</style>
