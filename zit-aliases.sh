fzif () {
  find $HOME/.zit/ -type f -name "*.csv" ! -name "*subtask*" | xargs -I {} basename -s .csv {} | fzf --preview="zit list -d {}" --preview-window=right:80% --layout=reverse --border
}
