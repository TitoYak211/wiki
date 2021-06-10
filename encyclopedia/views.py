import random
import re

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from . import util


def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })


def edit(request, title):
    if request.method == "POST":
        content = request.POST["content"]
        util.save_entry(title, content)
        return HttpResponseRedirect(reverse("entry", args=(title,)))
    content = util.get_entry(title)
    if content is None:
        return render(request, "encyclopedia/not_found.html")
    return render(request, "encyclopedia/edit.html", {
        "title": title,
        "markdown": content
    })


def entry(request, title):
    content = util.get_entry(title)
    if content is None:
        return render(request, "encyclopedia/not_found.html")

    # Handle bold
    content = re.sub(r"\*\*(.*?)\*\*", "<strong>\\1</strong>", content)

    # Handle links
    content = re.sub(r"\[(.*?)\]\((.*?)\)", "<a href=\"\\2\">\\1</a>", content)

    # Split content into lines
    lines = content.splitlines()

    # Assemble result
    html = ""
    current_list = None
    for line in lines:

        # Handle continuations of lists
        if current_list is not None:
            if line.startswith("* "):
                current_list += f"<li>{line[2:]}</li>"
                continue
            else:
                current_list += "</ul>"
                html += current_list
                current_list = None

        # Handle headings
        if line.startswith("#"):
            count = 0
            for i in range(6):
                if line[i] == "#":
                    count += 1
                else:
                    break
            html += f"<h{count}>{line.lstrip('# ')}</h{count}>"

        # Handle start of lists
        elif current_list is None and line.startswith("* "):
            current_list = f"<ul><li>{line[2:]}</li>"

        # Handle ordinary paragraphs
        else:
            html += f"<p>{line}</p>"

    # Handle lists at end of page
    if current_list is not None:
        current_list += "</ul>"
        html += current_list

    return render(request, "encyclopedia/entry.html", {
        "title": title,
        "html": html
    })


def new(request):
    if request.method == "POST":
        content = request.POST["content"]
        title = request.POST["title"]
        if util.get_entry(title):
            return render(request, "encyclopedia/error.html", {
                "message": "Page with that title already exists."
            })
        util.save_entry(title, content)
        return HttpResponseRedirect(reverse("entry", args=(title,)))
    return render(request, "encyclopedia/new.html")


def random_page(request):
    entries = util.list_entries()
    choice = random.choice(entries)
    return HttpResponseRedirect(reverse("entry", args=(choice,)))


def search(request):
    query = request.GET.get("q", "")
    if util.get_entry(query):
        return HttpResponseRedirect(reverse("entry", args=(query,)))
    results = [entry for entry in util.list_entries()
               if query.lower() in entry.lower()]
    return render(request, "encyclopedia/results.html", {
        "query": query,
        "results": list(sorted(results))
    })
