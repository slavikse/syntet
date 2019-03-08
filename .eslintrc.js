module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    'plugin:vue/recommended',
    '@vue/airbnb',
  ],
  rules: {
    'no-console': 'off',
    'no-param-reassign': 'off',
    'object-curly-newline': 'off',
    'vue/no-use-v-if-with-v-for': 'error',
    'vue/no-v-html': 'warning',
    'vue/html-closing-bracket-spacing': 'error',
    'vue/prop-name-casing': 'error',
  },
  parserOptions: {
    parser: 'babel-eslint',
  },
};
