# Karafun fair scheduler

Usage is simple:

```shell
$ pip install -r requirement.txt
$ python main.py 123456
```

The scheduler will connect to Karafun and manage your queue. Your guests can queue music as usual and the scheduler will automatically reorder them for fairness.

The algorithm is simple: Alice's second song in the queue will be between Bob's first and third song in the queue. For the rest it's FIFO.

You must turn on "Ask singer's name when adding to queue" in the Karafun remote control settings in order for the scheduler to work. If you don't actually want the names visible, pass `--hide-singers` when invoking the tool.

## Tricks

To move a song to be on the next list, just invoke

```bash
#curl 127.0.0.1:8080/next/<current_position>
curl 127.0.0.1:8080/next/4
```

## OBS

You can display a list of the next five singers by going to `http://127.0.0.1/`

## Dump current queue

Just use `http://127.0.0.1/json`

## Known issues / limitations

If you enable `--hide-singers`, the tool will deduplicate any songs that are queued twice (leaving only the first in the queue). This might be a feature for some, but a problem for others.

`--hide-singers` doesn't work for Community Songs, only for songs from the Karafun catalog.

If you enable `--hide-singers`, restarting the tool without emptying the queue will cause undefined behavior.
