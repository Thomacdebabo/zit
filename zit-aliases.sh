fzitls () {
find $HOME/.zit/ -type f -name "*.csv" ! -name "*subtask*" | xargs -I {} basename -s .csv {} | sort -r | fzf --preview="zit list -d {}" --preview-window=right:80% --border
}
fzitst () {
find $HOME/.zit/ -type f -name "*.csv" ! -name "*subtask*" | xargs -I {} basename -s .csv {} | sort -r | fzf --preview="zit status -d {}" --preview-window=right:80% --border
}

alias zitls="zit list"
alias zitst="zit status"

alias zlunch="zit lunch"
alias zstop="zit stop"
alias zstart="zit start"

alias zrm="zit remove"
alias zch="zit change"