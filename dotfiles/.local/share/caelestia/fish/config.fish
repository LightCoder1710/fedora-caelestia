if status is-interactive
    # Tắt câu chào mặc định của fish shell
    set -g fish_greeting ""

    # Starship custom prompt
    starship init fish | source

    # Custom colours
    cat ~/.local/state/caelestia/sequences.txt 2> /dev/null

    # For jumping between prompts in foot terminal
    function mark_prompt_start --on-event fish_prompt
        echo -en "\e]133;A\e\\"
    end

    # Dòng duy nhất để gọi ảnh ngẫu nhiên:
    bash ~/.random_ascii.sh
end
