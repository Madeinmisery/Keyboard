<template>
  <h4> {{ label }} </h4>
  <select
    class="list-box"
    :size="modelValue.length + 1"
    :value="selected"
    v-bind="$attrs"
  >  
    <option
      v-for="build in modelValue"
      :key="build"
    >
      {{ build }}
    </option>
  </select>
  <v-btn
    class="my-2"
    @click="deleteSelected"
  >
    Remove selected item
  </v-btn>
</template>

<script>
export default {
  props: {
    label: {
      type: String,
      required: true
    },
    modelValue: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      selected: null
    }
  },
  methods: {
    deleteSelected() {
      let deleteIndex = this.modelValue.indexOf(this.selected)
      if (deleteIndex>0) {
        this.$emit(
          "update:modelValue",
          this.modelValue.slice(0, deleteIndex))
          .concat(this.modelValue.slice(deleteIndex+1, -1))
      } else {
        this.$emit(
          "update:modelValue",
          this.modelValue.slice(1, -1)
        )
      }
    }
  }
}
</script>

<style scoped>
.list-box {
  width: 100%;
}
</style>