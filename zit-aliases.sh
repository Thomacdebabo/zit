zitls () {
find $HOME/.zit/ -type f -name "*.csv" ! -name "*subtask*" | xargs -I {} basename -s .csv {} | sort -r | fzf --preview="zit list -d {}" --preview-window=right:80% --border
}
zitst () {
find $HOME/.zit/ -type f -name "*.csv" ! -name "*subtask*" | xargs -I {} basename -s .csv {} | sort -r | fzf --preview="zit status -d {}" --preview-window=right:80% --border
}