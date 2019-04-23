<ul> -> @?
</ul> -> ?@
<li> -> @-
</li> -> -@
\n -> @^

- How to return json in flask

obj = {
    "ul": 2,
    "il": {
        "0" : 1,
        "1" : 3,
        "2" : 5
    },
    "message": {
        "0": "Message bukan ul",
        "1": {
            "0": "Message ul 1",
            "1": "Message ul 1 li 1",
            "2": "Message ul 1 li 2",
            "3": "Message ul 1 li 3"
        },
        "2": {
            "0": "Message ul 2",
            "1": "Message ul 2 li 1",
            "2": "Message ul 2 li 2",
            "3": "Message ul 2 li 3",
            "4": "Message ul 2 li 4",
            "5": "Message ul 2 li 5"
        }
    }
}

obj = {
    "ul": 0,
    "il": {
        "0" : 1
    },
    "message": {
        "0": "Message bukan ul"
    }
}

obj = {
    "ul": 2,
    "il": {
        "0" : 1,
        "1" : 3
    },
    "message": {
        "0": "<blank>",
        "1": {
            "0": "Message ul 1",
            "1": "Message ul 1 li 1",
            "2": "Message ul 1 li 2",
            "3": "Message ul 1 li 3"
        }
    }
}
