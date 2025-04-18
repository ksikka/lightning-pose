<template>
  <q-dialog :model-value="isDialogOpen">
    <q-card>
      <div class="text-h6">Create new model</div>
      <!-- Name -->
      <q-card-section>
        <q-input v-model="formData.name" label="Model Name" dense="true" hint="Used to name the model directory" />
      </q-card-section>

      <!-- Model Type Selection -->
      <q-expansion-item label="Model Type" header-class="text-h6" default-opened>
        <q-card-section>
          <q-list>
            <q-item tag="label" v-if="!editMode">
              {{ modelTypes[0].label }}
            </q-item>
            <q-item v-for="model in modelTypes" tag="label" v-ripple v-if="editMode">
              <q-item-section avatar>
                <q-radio
                  v-model="formData.model_type"
                  :val="model.value"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ model.label }}</q-item-label>
                <q-item-label caption>{{ model.caption }}</q-item-label>
              </q-item-section>
            </q-item>
            <q-item tag="label" v-ripple>
              <q-item-section avatar>
                <q-checkbox v-model="formData.has_unsupervised_losses" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Use unsupervised learning</q-item-label>
                <q-item-label caption>Generally helpful, but this should be tested against a supervised model.</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-expansion-item>

      <!-- Losses Selection-->
      <q-expansion-item label="Unsupervised Losses" header-class="text-h6" default-opened v-if="formData.has_unsupervised_losses">
        <q-card-section>
          <q-list>
            <q-item v-for="option in losses" tag="label" v-ripple>
              <q-item-section avatar>
                <q-checkbox
                  v-model="formData.losses"
                  :val="option.value"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ option.label }}</q-item-label>
                <q-item-label caption>{{ option.caption }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-expansion-item>

      <q-expansion-item label="Extended Configuration" header-class="text-h6">
      </q-expansion-item>


      <!-- Action Buttons -->
      <q-card-actions align="right">
        <q-btn label="Create" color="primary" @click="handleCreate" />
        <q-btn label="Cancel" color="secondary" flat @click="handleCancel" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script>
export default {
  name: "NewModelDialog",
  props: {
    modelData: {
      type: Object,
      required: true,
    },
    isDialogOpen: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      editMode: false,
      formData: {
        name: this.modelData.name || "",
        model_type: this.modelData.model_type || "supervised",
        has_unsupervised_losses: this.modelData.losses || false,
        losses: this.modelData.losses || [],
      },
      modelTypes: [
        {
          value: "heatmap",
          label: "Standard",
          caption: "A good starting point to establish baseline performance.",
        },
        {
          value: "heatmap_mhcrnn",
          label: "Context",
          caption: "Fancy model that may perform better but more GPU-intensive.",
        },
        // Add other model types as needed
      ],
      losses: [
        {
          value: "pca_singleview",
          label: "PCA Pose",
          caption: "Penalizes unlikely predictions using PCA analysis of the labeled data.",
        },
        {
          value: "temporal",
          label: "Temporal",
          caption: "Penalizes large jumps.",
        },
        {
          value: "pca_multiview",
          label: "PCA Multiview",
          caption: "Penalizes predictions that are inconsistent across views.",
        },
      ],
    };
  },
  methods: {
    handleCreate() {
      this.$emit("submit", this.formData);
    },
    handleCancel() {
      this.$emit("cancel");
    },
  },
};
</script>

<style scoped>
/* Optional: Styling specific to the dialog */
</style>
