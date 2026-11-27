set +x
setopt pipefail

gocode_get() {
    print -r -- "Authorization: Bearer $GOCODE_API_KEY" |
        command curl --disable --silent --fail --proto '=https' --connect-timeout 3 \
            --max-time 8 --header @- "$@"
}

case ${1:-} in
    gocode)
        if [[ -z ${GOCODE_API_KEY:-} || -z ${GOCODE_BASE_URL:-} ]]; then
            [[ ${2:-} != --from-interactive-shell ]] || exit 78
            # GUI launches may only see the GoCode exports after .zshrc runs.
            exec /bin/zsh -ic 'exec /bin/zsh -f "$1" gocode --from-interactive-shell >&3 2>&4' \
                godaddy-ai "${0:A}" 3>&1 4>&2 >/dev/null 2>&1
        fi

        base_url=${GOCODE_BASE_URL%/}
        key_info=$(gocode_get --url "$base_url/key/info") || exit $?
        key_budget=$(print -r -- "$key_info" | command jq -ce '
            .info | objects | select(.spend | type == "number")
            | {spend, max_budget: (.max_budget | numbers // null)}
        ') || exit $?

        # GoCode can assign the monthly budget to the key's owner.
        if user_id=$(print -r -- "$key_info" | command jq -er '
            .info | select((.max_budget | type) != "number")
            | .user_id | strings | select(length > 0)
        ') && user_budget=$(gocode_get --get --url "$base_url/user/info" --data-urlencode "user_id=$user_id" |
            command jq -ce '
                .user_info | objects
                | select((.spend | type) == "number" and (.max_budget | type) == "number")
                | {spend, max_budget}
            '); then
            print -r -- "$user_budget"
        else
            print -r -- "$key_budget"
        fi
        ;;
    cursor)
        [[ -n ${CURSOR_TEAM_ID:-} && -n ${CURSOR_SESSION:-} ]] || exit 78
        print -r -- "Cookie: WorkosCursorSessionToken=$CURSOR_SESSION" |
            command curl --disable --silent --fail --proto '=https' --connect-timeout 3 \
                --max-time 8 --header @- --get --data-urlencode "teamId=$CURSOR_TEAM_ID" \
                --url 'https://cursor.com/api/usage-summary' |
            command jq -ce '
                .individualUsage.overall | objects
                | select((.used | type) == "number" and (.limit | type) == "number")
                | {spend: (.used / 100), max_budget: (.limit / 100)}
            '
        ;;
    *)
        exit 64
        ;;
esac
