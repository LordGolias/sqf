#include <string>
#include <vector>
#include <map>
#include <set>
#include <assert.h>

using namespace std;

typedef map<string, string> string_map;
typedef map<string, set<string> > string_set_map;

pair<string, string> rsplit(string const & sequence, string const & term) {
    string prefix = sequence.substr(0, sequence.rfind(term));
    string suffix = sequence.substr(sequence.rfind(term) + term.size(), sequence.size());
    return pair<string, string>(prefix, suffix);
}

bool startswith(string const & a, string const & b) {
    return a.compare(0, b.length(), b) == 0;
}

vector<string> tokenize(string const & text, vector<string> const & keyterms) {

    vector<string> result;
    string_set_map string_usages;
    string_map usages;
    set<string> matches;

    string sequence;
    for(unsigned int char_i = 0; char_i < text.size(); char_i++) {
        char character = text[char_i];
        sequence += character;

        for(unsigned int term_i = 0; term_i < keyterms.size(); term_i++) {
            string const & term = keyterms[term_i];
            string current_string = string(1, character);

            string_map::const_iterator term_usage = usages.find(term);
            if (term_usage != usages.end())
                current_string = term_usage->second + current_string;

            set<string>::const_iterator term_match = matches.find(term);
            // if term not in matches
            if (term_match == matches.end()) {
                // if term.startswith(current_string)
                if (startswith(term, current_string)) {
                    // the term uses current_string; update the references list to current_string.

                    // if term in usages
                    if (term_usage != usages.end()) {
                        string_usages[term_usage->second].erase(term);
                        if (string_usages[term_usage->second].empty())
                            string_usages.erase(term_usage->second);
                    }
                    usages[term] = current_string;
                    string_usages[current_string].insert(term);
                }
                else { // failed to match current_string
                    // clean references
                    if (term_usage != usages.end()) {
                        string_usages[term_usage->second].erase(term);
                        if (string_usages[term_usage->second].empty())
                            string_usages.erase(term_usage->second);
                        usages.erase(term);
                    }
                }
            }

            if (term == current_string) {
                matches.insert(term);
            }
        } // for (string term : keyterms)

        // pick the longest candidate, if any
        string candidate;
        for (set<string>::const_iterator it = matches.begin(); it != matches.end(); ++it) {
            string const& match = *it;
            assert(string_usages.count(match) == 1);
            assert(usages.count(match) == 1);
            if (string_usages[match].size() > 1)
                continue;
            bool invalid = false;
            for (string_set_map::const_iterator string_usage = string_usages.begin(); string_usage != string_usages.end(); string_usage++) {
                if (string_usage->first != match and string_usage->first.find(match) != string::npos) {
                    invalid = true;
                    break;
                }
            }
            if (invalid)
                continue;

            if (match.size() > candidate.size())
                candidate = match;
        }

        if (candidate.size()) {
            string const &term = candidate;
            pair<string, string> split = rsplit(sequence, term);
            string prefix = split.first;
            string suffix = split.second;

            if (prefix.size() > 0) {
                vector<string> prefix_result = tokenize(prefix, keyterms);
                // copy prefix_result to result.
                result.insert(result.end(), prefix_result.begin(), prefix_result.end());
            }
            result.push_back(term);

            // remove all usages that were part of the yielded in term
            string_set_map copy_string_usages(string_usages); // a copy because we change `string_usages`
            for (string_set_map::const_iterator string_usage = copy_string_usages.begin(); string_usage != copy_string_usages.end(); string_usage++) {
                if (term.find(string_usage->first) != string::npos) {
                    for (set<string>::const_iterator usage = string_usage->second.begin(); usage != string_usage->second.end(); usage++)
                        usages.erase(*usage);
                    string_usages.erase(string_usage->first);
                }
                if (matches.count(string_usage->first))
                    matches.erase(string_usage->first);
            }
            sequence = suffix;
        }
    }

    for (set<string>::const_iterator it = matches.begin(); it != matches.end(); ++it) {
        string const& match = *it;
        pair<string, string> split = rsplit(sequence, match);
        string prefix = split.first;
        string suffix = split.second;
        result.push_back(prefix);
        result.push_back(match);
        sequence = suffix;
    }
    if (sequence.size())
        result.push_back(sequence);

    return result;
};
