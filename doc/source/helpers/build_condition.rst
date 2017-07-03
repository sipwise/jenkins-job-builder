================== ====================================================
Condition kind     Description
================== ====================================================
always             Condition is always verified
never              Condition is never verified
boolean-expression Run the step if the expression expends to a
                   representation of true

                     :condition-expression: Expression to expand (required)
build-cause        Run if the current build has a specific cause

                     :cause: The cause why the build was triggered.
                       Following causes are supported -

                       :USER_CAUSE: build was triggered by a manual
                         interaction. (default)
                       :SCM_CAUSE: build was triggered by a SCM change.
                       :TIMER_CAUSE: build was triggered by a timer.
                       :CLI_CAUSE: build was triggered by via CLI interface
                       :REMOTE_CAUSE: build was triggered via remote
                         interface.
                       :UPSTREAM_CAUSE: build was triggered by an upstream
                         project.

                       Following supported if XTrigger plugin installed:

                       :FS_CAUSE: build was triggered by a file system
                         change (FSTrigger Plugin).
                       :URL_CAUSE: build was triggered by a URL change
                         (URLTrigger Plugin)
                       :IVY_CAUSE: build triggered by an Ivy dependency
                         version has change (IvyTrigger Plugin)
                       :SCRIPT_CAUSE: build was triggered by a script
                         (ScriptTrigger Plugin)
                       :BUILDRESULT_CAUSE: build was triggered by a
                         result of an other job (BuildResultTrigger Plugin)
                     :exclusive-cause: (bool) There might by multiple
                       casues causing a build to be triggered, with
                       this true, the cause must be the only one
                       causing this build this build to be triggered.
                       (default false)
day-of-week        Only run on specific days of the week.

                     :day-selector: Days you want the build to run on.
                       Following values are supported -

                       :weekend: Saturday and Sunday (default).
                       :weekday: Monday - Friday.
                       :select-days: Selected days, defined by 'days'
                         below.
                       :days: True for days for which the build should
                         run. Definition needed only for 'select-days'
                         day-selector, at the same level as day-selector.
                         Define the days to run under this.

                         :SUN: Run on Sunday (default false)
                         :MON: Run on Monday (default false)
                         :TUES: Run on Tuesday (default false)
                         :WED: Run on Wednesday (default false)
                         :THURS: Run on Thursday (default false)
                         :FRI: Run on Friday (default false)
                         :SAT: Run on Saturday (default false)
                     :use-build-time: (bool) Use the build time instead of
                       the the time that the condition is evaluated.
                       (default false)
execution-node     Run only on selected nodes.

                     :nodes: (list) List of nodes to execute on. (required)
strings-match      Run the step if two strings match

                     :condition-string1: First string (optional)
                     :condition-string2: Second string (optional)
                     :condition-case-insensitive: Case insensitive
                       (default false)
current-status     Run the build step if the current build status is
                   within the configured range

                     :condition-worst: Accepted values are SUCCESS,
                       UNSTABLE, FAILURE, NOT_BUILD, ABORTED
                       (default SUCCESS)
                     :condition-best: Accepted values are SUCCESS,
                       UNSTABLE, FAILURE, NOT_BUILD, ABORTED
                       (default SUCCESS)

shell              Run the step if the shell command succeed

                     :condition-command: Shell command to execute
                       (optional)
windows-shell      Similar to shell, except that commands will be
                   executed by cmd, under Windows

                     :condition-command: Command to execute (optional)

file-exists        Run the step if a file exists

                     :condition-filename: Check existence of this file
                       (required)
                     :condition-basedir: If condition-filename is
                       relative, it will be considered relative to
                       either `workspace`, `artifact-directory`,
                       or `jenkins-home`. (default 'workspace')
files-match        Run if one or more files match the selectors.

                     :include-pattern: (list str) List of Includes
                       Patterns. Since the separator in the patterns is
                       hardcoded as ',', any use of ',' would need
                       escaping. (optional)
                     :exclude-pattern: (list str) List of Excludes
                       Patterns. Since the separator in the patterns is
                       hardcoded as ',', any use of ',' would need
                       escaping. (optional)
                     :condition-basedir: Accepted values are `workspace`,
                       `artifact-directory`, or `jenkins-home`.
                       (default 'workspace')
num-comp           Run if the numerical comparison is true.

                     :lhs: Left Hand Side. Must evaluate to a number.
                       (required)
                     :rhs: Right Hand Side. Must evaluate to a number.
                       (required)
                     :comparator: Accepted values are `less-than`,
                       `greater-than`, `equal`, `not-equal`,
                       `less-than-equal`, `greater-than-equal`.
                       (default 'less-than')
regexp             Run the action if a regular expression matches

                     :condition-expression: Regular Expression
                     :condition-searchtext: Text to match against
                       the regular expression
regex-match        Run if the Expression matches the Label.

                     :regex: The regular expression used to match the label
                       (optional)
                     :label: The label that will be tested by the regular
                       expression. (optional)
time               Only run during a certain period of the day.

                     :earliest-hour: Starting hour (default "09")
                     :earliest-min: Starting min (default "00")
                     :latest-hour: Ending hour (default "17")
                     :latest-min: Ending min (default "30")
                     :use-build-time: (bool) Use the build time instead of
                       the the time that the condition is evaluated.
                       (default false)
not                Run the step if the inverse of the condition-operand
                   is true

                     :condition-operand: Condition to evaluate.  Can be
                       any supported conditional-step condition. (required)
and                Run the step if logical and of all conditional-operands
                   is true

                     :condition-operands: (list) Conditions to evaluate.
                       Can be any supported conditional-step condition.
                       (required)
or                 Run the step if logical or of all conditional-operands
                   is true

                     :condition-operands: (list) Conditions to evaluate.
                       Can be any supported conditional-step condition.
                       (required)
================== ====================================================
