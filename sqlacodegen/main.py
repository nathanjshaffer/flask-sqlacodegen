""" """
from __future__ import unicode_literals, division, print_function, absolute_import
import argparse
import codecs
import importlib
import sys
import os
import time

from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData

from sqlacodegen.codegen import CodeGenerator
import sqlacodegen
import sqlacodegen.dialects


def import_dialect_specificities(engine):
    dialect_name = '.' + engine.dialect.name
    try:
        importlib.import_module(dialect_name, 'sqlacodegen.dialects')
    except ImportError:
        pass


def main():
    parser = argparse.ArgumentParser(description='Generates SQLAlchemy model code from an existing database.')
    parser.add_argument('url', nargs='?', help='SQLAlchemy url to the database')
    parser.add_argument('--version', action='store_true', help="print the version number and exit")
    parser.add_argument('--schema', help='load tables from an alternate schema')
    parser.add_argument('--default-schema', help='default schema name for local schema object')
    parser.add_argument('--tables', help='tables to process (comma-separated, default: all)')
    parser.add_argument('--noviews', action='store_true', help="ignore views")
    parser.add_argument('--noindexes', action='store_true', help='ignore indexes')
    parser.add_argument('--noconstraints', action='store_true', help='ignore constraints')
    parser.add_argument('--nojoined', action='store_true', help="don't autodetect joined table inheritance")
    parser.add_argument('--noinflect', action='store_true', help="don't try to convert tables names to singular form")
    parser.add_argument('--noclasses', action='store_true', help="don't generate classes, only tables")
    parser.add_argument('--notables', action='store_true', help="don't generate tables, only classes")
    parser.add_argument('--outfile', help='file to write output to (default: stdout)')
    parser.add_argument('--nobackrefs', action='store_true', help="don't include backrefs")
    parser.add_argument('--flask', action='store_true', help="use Flask-SQLAlchemy columns")
    parser.add_argument('--ignore-cols', help="Don't check foreign key constraints on specified columns (comma-separated)")
    parser.add_argument('--nocomments', action='store_true', help="don't render column comments")
    parser.add_argument('--flask-endpoint-conf', help="config file for flask endpoints")
    parser.add_argument('--flask-endpoint-outfile', help="output file to write flask endpoint classes")
    parser.add_argument('--apiflask-endpoint', help="add apiFLASK functionality to generated endpoints.  use with '--flask-endpoint-outfile' option")
    parser.add_argument('--dataclass', action='store_true', help="add dataclass decorators for JSON serialization")
    args = parser.parse_args()

    if args.version:
        print(sqlacodegen.version)
        return
    if not args.url:
        print('You must supply a url\n', file=sys.stderr)
        parser.print_help()
        return

    endpoint_conf = args.flask_endpoint_conf
    if args.flask_endpoint_outfile:

        if not endpoint_conf:

            endpoint_conf =  'endpointgen_conf'
        if not os.path.isfile(endpoint_conf):
            file = open(endpoint_conf,'w+')
            str = '{"resourceClass" : "Resource",\n'
            str += '"modelModule" : "models",\n'
            str += '"decorators" : [],\n'
            str += '"dbObject" : "db",\n'
            str += '"addResourceFunction" : "api.add_resource",\n'
            str += '"apiUrlPrefix" : ""\n}'
            file.write(str)
            file.close
            time.sleep(3)

    default_schema = args.default_schema
    if not default_schema:
        default_schema = None

    engine = create_engine(args.url)
    import_dialect_specificities(engine)
    metadata = MetaData()
    tables = args.tables.split(',') if args.tables else None
    ignore_cols = args.ignore_cols.split(',') if args.ignore_cols else None
    metadata.reflect(engine, args.schema, not args.noviews, tables)
    outfile = codecs.open(args.outfile, 'w', encoding='utf-8') if args.outfile else sys.stdout
    generator = CodeGenerator(metadata, args.noindexes, args.noconstraints,
                              args.nojoined, args.noinflect, args.nobackrefs,
                              args.flask, ignore_cols, args.noclasses, args.nocomments, args.notables, args.dataclass, args.apiflask_endpoint)
    generator.render(outfile)

    if args.flask_endpoint_outfile:

        outfile = open(args.flask_endpoint_outfile,'w+')
        generator.renderEndpoints(endpoint_conf, outfile)


if __name__ == '__main__':
    main()
