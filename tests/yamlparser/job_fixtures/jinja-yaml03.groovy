if (manager.logContains(".*no_jenkins.*")) {
    manager.build.result = hudson.model.Result.NOT_BUILT
}
