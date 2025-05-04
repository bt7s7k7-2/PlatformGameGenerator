target_dir="release.local"
repository_url="git@github.com:bt7s7k7-2/PlatformGameGenerator.git"

if [ ! -d "$target_dir" ]; then
    git clone -b docs "$repository_url" "$target_dir"
else
    echo "Directory '$target_dir' already exists. Skipping clone."
fi

cd "$target_dir"
git pull
cd -

cp docs/index.pdf docs/index_*.pdf dist/* "$target_dir"

cd "$target_dir"
git add .
git commit --amend --no-edit
git push --force
cd -
