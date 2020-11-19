HTML Generator
==============

A python package to generate HTML from a template which is defined through a tree of render-objects.

Gettings started
----------------

Installing:

    pip install htmlgenerator

A simple example:

    import htmlgenerator

    my_page = htmlgenerator.HTML(htmlgenerator.BODY(htmlgenerator.H1("It works!")))

    htmlgenerator.render(my_page, {})


