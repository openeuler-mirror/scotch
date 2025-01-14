%global openmpidir %{_builddir}/ptscotch-openmpi-%{version}-%{release}
%global mpichdir %{_builddir}/ptscotch-mpich-%{version}-%{release}

# Shared library versioning:
# Increment if interface is changed in an incompatible way
%global so_maj 1
# Increment if interface is extended
%global so_min 3

Name:          scotch
Summary:       Graph, mesh and hypergraph partitioning library
Version:       6.0.9
Release:       2

License:       CeCILL-C
URL:           https://gforge.inria.fr/projects/scotch/
Source0:       https://gforge.inria.fr/frs/download.php/file/38187/%{name}_%{version}.tar.gz
Source1:       scotch-Makefile.shared.inc.in

# Makefile fix for installing esmumps
Patch0:        scotch_esmumps.patch
# Make shared libraries link properly with -Wl,--as-needed
Patch1:        scotch-ldflags.patch
# Fix undefined man page macros
Patch2:        scotch-man.patch

BuildRequires: flex
BuildRequires: bison
BuildRequires: zlib-devel
BuildRequires: bzip2-devel
BuildRequires: xz-devel
BuildRequires: environment-modules

%description
Scotch is a software package for graph and mesh/hypergraph partitioning and
sparse matrix ordering. The parallel scotch libraries are packaged in the
ptscotch sub-packages.

%package devel
Summary:       Development libraries for scotch
Requires:      %{name}%{?_isa} = %{version}-%{release}

%description devel
This package contains development libraries for scotch.


%package doc
Summary:       Documentations and example for scotch and ptscotch
BuildArch:     noarch

%description doc
Contains documentations and example for scotch and ptscotch

###############################################################################

%package -n ptscotch-mpich
Summary:       PT-Scotch libraries compiled against mpich
BuildRequires: mpich-devel

%description -n ptscotch-mpich
Scotch is a software package for graph and mesh/hypergraph partitioning and
sparse matrix ordering. This sub-package provides parallelized scotch libraries
compiled with mpich.


%package -n ptscotch-mpich-devel
Summary:       Development libraries for PT-Scotch (mpich)
Requires:      pt%{name}-mpich%{?_isa} = %{version}-%{release}

%description -n ptscotch-mpich-devel
This package contains development libraries for PT-Scotch, compiled against
mpich.

%package -n ptscotch-mpich-devel-parmetis
Summary:       Parmetis compatibility header for scotch
Requires:      pt%{name}-mpich-devel%{?_isa} = %{version}-%{release}

%description -n ptscotch-mpich-devel-parmetis
This package contains the parmetis compatibility header for scotch.


###############################################################################

%package -n ptscotch-openmpi
Summary:       PT-Scotch libraries compiled against openmpi
BuildRequires: openmpi-devel

%description -n ptscotch-openmpi
Scotch is a software package for graph and mesh/hypergraph partitioning and
sparse matrix ordering. This sub-package provides parallelized scotch libraries
compiled with openmpi.


%package -n ptscotch-openmpi-devel
Summary:       Development libraries for PT-Scotch (openmpi)
Requires:      pt%{name}-openmpi%{?_isa} = %{version}-%{release}

%description -n ptscotch-openmpi-devel
This package contains development libraries for PT-Scotch, compiled against
openmpi.


%package -n ptscotch-openmpi-devel-parmetis
Summary:       Parmetis compatibility header for scotch
Requires:      pt%{name}-openmpi-devel%{?_isa} = %{version}-%{release}

%description -n ptscotch-openmpi-devel-parmetis
This package contains the parmetis compatibility header for scotch.

###############################################################################

%prep
# NOTE: If the archive prefix folder does not match %%{name}_%%{version}, then the file ID in the Source URL is likely wrong!
%autosetup -p1 -n %{name}_%{version}

cp -a %{SOURCE1} src/Makefile.inc

# Convert the license files to utf8
for file in doc/CeCILL-C_V1-en.txt doc/CeCILL-C_V1-fr.txt; do
    iconv -f iso8859-1 -t utf-8 $file > $file.conv && mv -f $file.conv $file
done

cp -a . %{openmpidir}
cp -a . %{mpichdir}


%build
pushd src/
make scotch esmumps CFLAGS="%{optflags}" LDFLAGS="%{?__global_ldflags}" SOMAJ="%{so_maj}"
popd

%{_mpich_load}
pushd %{mpichdir}/src/
make ptscotch ptesmumps CFLAGS="%{optflags}" LDFLAGS="%{?__global_ldflags} -L%{_libdir}/mpich/lib -lmpi" SOMAJ="%{so_maj}"
popd
%{_mpich_unload}

%{_openmpi_load}
pushd %{openmpidir}/src/
make ptscotch ptesmumps CFLAGS="%{optflags}" LDFLAGS="%{?__global_ldflags} -L%{_libdir}/openmpi/lib -lmpi" SOMAJ="%{so_maj}"
popd
%{_openmpi_unload}


%install
%define doinstall() \
make install prefix=%{buildroot}${MPI_HOME} libdir=%{buildroot}${MPI_LIB} includedir=%{buildroot}${MPI_INCLUDE} mandir=%{buildroot}${MPI_MAN} bindir=%{buildroot}${MPI_BIN} \
# Fix debuginfo packages not finding sources (See libscotch/Makefile) \
ln -s parser_ll.c libscotch/lex.yy.c \
ln -s parser_yy.c libscotch/y.tab.c \
ln -s parser_ly.h libscotch/y.tab.h \
\
pushd %{buildroot}${MPI_LIB}; \
for lib in *.so; do \
    chmod 755 $lib \
    mv $lib $lib.%{so_maj}.%{so_min} && ln -s $lib.%{so_maj}.%{so_min} $lib && ln -s $lib.%{so_maj}.%{so_min} $lib.%{so_maj} \
done \
popd \
\
pushd %{buildroot}${MPI_BIN} \
for prog in *; do \
    mv $prog scotch_${prog} \
    chmod 755 scotch_$prog \
done \
popd \
\
pushd %{buildroot}${MPI_MAN}/man1/ \
for man in *; do \
    mv ${man} scotch_${man} \
done \
# Cleanup man pages (some pages are only relevant for ptscotch packages, and vice versa) \
for man in *; do \
  if [ ! -f %{buildroot}${MPI_BIN}/${man/.1/} ]; then \
    rm -f $man \
  fi \
done \
popd

###############################################################################

export MPI_HOME=%{_prefix}
export MPI_LIB=%{_libdir}
export MPI_INCLUDE=%{_includedir}
export MPI_MAN=%{_mandir}
export MPI_BIN=%{_bindir}
pushd src
%doinstall
popd

###############################################################################

%{_mpich_load}
pushd %{mpichdir}/src
%doinstall
install -m644 libscotchmetis/parmetis.h %{buildroot}${MPI_INCLUDE}
popd
%{_mpich_unload}

###############################################################################

%{_openmpi_load}
pushd %{openmpidir}/src
%doinstall
install -m644 libscotchmetis/parmetis.h %{buildroot}${MPI_INCLUDE}
popd
%{_openmpi_unload}

###############################################################################


%check
LD_LIBRARY_PATH=%{buildroot}%{_libdir} make -C src/check


%ldconfig_scriptlets

%ldconfig_scriptlets -n ptscotch-mpich

%ldconfig_scriptlets -n ptscotch-openmpi


%{!?_licensedir:%global license %%doc}
%files
%license doc/CeCILL-C_V1-en.txt
%{_bindir}/*
%{_libdir}/libscotch*.so.1*
%{_libdir}/libesmumps*.so.1*
%{_mandir}/man1/*

%files devel
%{_libdir}/libscotch*.so
%{_libdir}/libesmumps*.so
%{_includedir}/*scotch*.h
%{_includedir}/*esmumps*.h

%files -n ptscotch-mpich
%license doc/CeCILL-C_V1-en.txt
%{_libdir}/mpich/lib/lib*scotch*.so.1*
%{_libdir}/mpich/lib/lib*esmumps*.so.1*
%{_libdir}/mpich/bin/*
%{_mandir}/mpich*/*

%files -n ptscotch-mpich-devel
%{_includedir}/mpich*/*scotch*.h
%{_includedir}/mpich*/*esmumps*.h
%{_libdir}/mpich/lib/lib*scotch*.so
%{_libdir}/mpich/lib/lib*esmumps*.so

%files -n ptscotch-mpich-devel-parmetis
%{_includedir}/mpich*/parmetis.h

%files -n ptscotch-openmpi
%license doc/CeCILL-C_V1-en.txt
%{_libdir}/openmpi/lib/lib*scotch*.so.1*
%{_libdir}/openmpi/lib/lib*esmumps*.so.1*
%{_libdir}/openmpi/bin/*
%{_mandir}/openmpi*/*

%files -n ptscotch-openmpi-devel
%{_includedir}/openmpi*/*scotch*.h
%{_includedir}/openmpi*/*esmumps*.h
%{_libdir}/openmpi/lib/lib*scotch*.so
%{_libdir}/openmpi/lib/lib*esmumps*.so

%files -n ptscotch-openmpi-devel-parmetis
%{_includedir}/openmpi*/parmetis.h

%files doc
%license doc/CeCILL-C_V1-en.txt
%doc doc/*.pdf
%doc doc/scotch_example.f

%changelog
* Tue Jan 14 2025 QiuWenjian <wenjian.oerv@isrc.iscas.ac.cn> - 6.0.9-2
- Fix compile error

* Wed Jun 15 2022 lvxiaoqian <xiaoqian@nj.iscas.ac.cn> - 6.0.9-1
- init package